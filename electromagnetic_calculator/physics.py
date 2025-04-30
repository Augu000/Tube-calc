from dataclasses import dataclass
from typing import Optional, Generator
import numpy as np
from pydantic import BaseModel, Field
import plotly.graph_objects as go

# Constants
MU_0 = 4 * np.pi * 1e-7  # Permeability of free space (T·m/A)
COPPER_RESISTIVITY = 1.68e-8  # Ω·m at 20°C
COPPER_DENSITY = 8960  # kg/m³
PVC_DENSITY = 1380  # kg/m³
NEODYMIUM_DENSITY = 7500  # kg/m³

class MagnetSpecs(BaseModel):
    """Specifications for the magnet"""
    diameter: float = Field(..., description="Diameter of the magnet in meters")
    length: float = Field(..., description="Length of the magnet in meters")
    magnetic_field: float = Field(..., description="Magnetic field strength in Tesla")
    material: str = Field("NdFeB", description="Magnet material type")

class CoilSpecs(BaseModel):
    """Specifications for the coil"""
    inner_diameter: float = Field(..., description="Inner diameter of the coil in meters")
    outer_diameter: float = Field(..., description="Outer diameter of the coil in meters")
    length: float = Field(..., description="Length of the coil in meters")
    wire_diameter: float = Field(..., description="Diameter of the wire in meters")
    turns: int = Field(..., description="Number of turns in the coil")
    material: str = Field("Copper", description="Wire material type")
    awg: Optional[int] = Field(None, description="American Wire Gauge number")
    permeability: float = Field(1.0, description="Relative permeability of core material")

class TubeSpecs(BaseModel):
    """Specifications for the tube"""
    inner_diameter: float = Field(..., description="Inner diameter of the tube in meters")
    length: float = Field(..., description="Length of the tube in meters")
    pipe_thickness: float = Field(0.004, description="Wall thickness of the pipe in meters")
    material: str = Field("PVC", description="Tube material type")

class SystemSpecs(BaseModel):
    """Complete system specifications"""
    magnet: MagnetSpecs
    coil: CoilSpecs
    tube: TubeSpecs
    velocity: float = Field(..., description="Velocity of the magnet in m/s")

class CoilConnection(BaseModel):
    """Model for different coil connection configurations"""
    type: str = Field(..., description="Connection type: 'series', 'parallel', or 'series_parallel'")
    series_groups: int = Field(1, description="Number of series-connected groups (for series_parallel)")
    parallel_coils: int = Field(1, description="Number of parallel coils per group (for series_parallel)")

    def calculate_total_resistance(self, single_coil_resistance: float) -> float:
        """Calculate total resistance based on connection type"""
        if self.type == "series":
            return single_coil_resistance * self.series_groups
        elif self.type == "parallel":
            return single_coil_resistance / self.parallel_coils
        else:  # series_parallel
            group_resistance = single_coil_resistance * self.series_groups
            return group_resistance / self.parallel_coils

    def calculate_total_voltage(self, single_coil_voltage: float) -> float:
        """Calculate total voltage based on connection type"""
        if self.type == "series":
            return single_coil_voltage * self.series_groups
        elif self.type == "parallel":
            return single_coil_voltage
        else:  # series_parallel
            return single_coil_voltage * self.series_groups

    def calculate_total_current(self, single_coil_current: float) -> float:
        """Calculate total current based on connection type"""
        if self.type == "series":
            return single_coil_current
        elif self.type == "parallel":
            return single_coil_current * self.parallel_coils
        else:  # series_parallel
            return single_coil_current * self.parallel_coils

def calculate_required_turns(target_voltage: float, magnetic_field: float, 
                           coil_area: float, velocity: float, coil_length: float) -> int:
    """
    Calculate required number of turns using Faraday's Law:
    N = (V * L) / (B * A * v)
    """
    return int(np.ceil((target_voltage * coil_length) / (magnetic_field * coil_area * velocity)))

def calculate_coil_area(inner_diameter: float, outer_diameter: float) -> float:
    """Calculate cross-sectional area of the coil"""
    return np.pi * ((outer_diameter/2)**2 - (inner_diameter/2)**2)

def calculate_wire_length(coil: CoilSpecs) -> float:
    """Calculate total wire length based on number of turns and average diameter"""
    avg_diameter = (coil.inner_diameter + coil.outer_diameter) / 2
    return np.pi * avg_diameter * coil.turns

def calculate_coil_resistance(coil: CoilSpecs) -> float:
    """Calculate the resistance of the coil using R = ρ * L / A"""
    wire_length = calculate_wire_length(coil)
    wire_area = np.pi * (coil.wire_diameter / 2)**2
    return COPPER_RESISTIVITY * wire_length / wire_area

def calculate_induced_voltage(system: SystemSpecs) -> float:
    """
    Calculate the induced voltage using Faraday's Law:
    V = N * B * A * v / L
    """
    coil_area = calculate_coil_area(system.coil.inner_diameter, system.coil.outer_diameter)
    return (system.coil.turns * system.magnet.magnetic_field * coil_area * 
            system.velocity / system.coil.length)

def calculate_induced_current(system: SystemSpecs) -> float:
    """Calculate the induced current using Ohm's Law: I = V/R"""
    voltage = calculate_induced_voltage(system)
    resistance = calculate_coil_resistance(system.coil)
    return voltage / resistance

def calculate_power(system: SystemSpecs) -> float:
    """Calculate the power generated: P = V * I"""
    voltage = calculate_induced_voltage(system)
    current = calculate_induced_current(system)
    return voltage * current

def optimize_coil_configuration(target_voltage: float, target_current: float,
                              magnet: MagnetSpecs, max_coils: int = 20) -> tuple[CoilSpecs, float]:
    """
    Find the optimal coil configuration that meets voltage and current requirements.
    Returns the best coil specs and required velocity.
    """
    best_config = None
    best_velocity = float('inf')
    best_efficiency = 0
    target_resistance = target_voltage / target_current  # Required resistance for target current
    
    # Try different magnet configurations first
    magnet_configs = [
        magnet,  # Original magnet
        MagnetSpecs(  # Stronger magnet
            diameter=magnet.diameter,
            length=magnet.length,
            magnetic_field=1.4,  # 1.4T
            material=magnet.material
        ),
        MagnetSpecs(  # Larger magnet
            diameter=magnet.diameter * 1.2,  # 20% larger
            length=magnet.length * 1.2,      # 20% longer
            magnetic_field=magnet.magnetic_field,
            material=magnet.material
        )
    ]
    
    for current_magnet in magnet_configs:
        # Try different number of coils
        for num_coils in range(1, max_coils + 1):
            # Try different wire diameters (in mm)
            for wire_diameter in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
                wire_diameter_m = wire_diameter / 1000  # Convert to meters
                
                # Try different coil lengths
                for coil_length in [0.1, 0.15, 0.2, 0.25, 0.3]:  # 100mm to 300mm
                    # Create initial coil
                    coil = CoilSpecs(
                        inner_diameter=current_magnet.diameter + 0.002,  # 2mm clearance
                        outer_diameter=current_magnet.diameter + 0.02,   # 20mm total thickness
                        length=coil_length,
                        wire_diameter=wire_diameter_m,
                        turns=0,  # Will be calculated
                        material="Copper"
                    )
                    
                    # Calculate coil area
                    coil_area = calculate_coil_area(coil.inner_diameter, coil.outer_diameter)
                    
                    # Try different velocities
                    for base_velocity in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
                        velocity = base_velocity
                        required_turns = calculate_required_turns(
                            target_voltage, current_magnet.magnetic_field, coil_area, velocity, coil.length
                        )
                        
                        # Update coil with calculated turns
                        coil.turns = required_turns
                        
                        # Calculate actual performance
                        system = SystemSpecs(
                            magnet=current_magnet,
                            coil=coil,
                            tube=TubeSpecs(
                                inner_diameter=coil.outer_diameter + 0.002,
                                length=coil.length * 1.2,
                                pipe_thickness=0.004,
                                material="PVC"
                            ),
                            velocity=velocity
                        )
                        
                        # Calculate actual voltage and current
                        actual_voltage = calculate_induced_voltage(system)
                        actual_current = calculate_induced_current(system)
                        
                        # Calculate resistance
                        resistance = calculate_coil_resistance(coil)
                        
                        # Check if we meet the target parameters
                        meets_voltage = abs(actual_voltage - target_voltage) / target_voltage < 0.01  # 1% tolerance
                        meets_current = abs(actual_current - target_current) / target_current < 0.01  # 1% tolerance
                        meets_resistance = abs(resistance - target_resistance) / target_resistance < 0.01  # 1% tolerance
                        
                        if meets_voltage and meets_current and meets_resistance:
                            # If we meet all targets, this is our best configuration
                            return coil, velocity
                        
                        # Calculate efficiency (how close to target values)
                        voltage_efficiency = 1 - abs(actual_voltage - target_voltage) / target_voltage
                        current_efficiency = 1 - abs(actual_current - target_current) / target_current
                        resistance_efficiency = 1 - abs(resistance - target_resistance) / target_resistance
                        total_efficiency = (voltage_efficiency + current_efficiency + resistance_efficiency) / 3
                        
                        # If this configuration is better, update best
                        if total_efficiency > best_efficiency:
                            best_efficiency = total_efficiency
                            best_config = coil
                            best_velocity = velocity
                            best_magnet = current_magnet
    
    # If we didn't find a perfect match, try to fine-tune the best configuration
    if best_config is not None:
        # Try adjusting the velocity to get closer to targets
        for velocity_adjustment in [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]:
            adjusted_velocity = best_velocity * velocity_adjustment
            system = SystemSpecs(
                magnet=best_magnet,
                coil=best_config,
                tube=TubeSpecs(
                    inner_diameter=best_config.outer_diameter + 0.002,
                    length=best_config.length * 1.2,
                    pipe_thickness=0.004,
                    material="PVC"
                ),
                velocity=adjusted_velocity
            )
            
            actual_voltage = calculate_induced_voltage(system)
            actual_current = calculate_induced_current(system)
            
            if (abs(actual_voltage - target_voltage) / target_voltage < 0.01 and
                abs(actual_current - target_current) / target_current < 0.01):
                return best_config, adjusted_velocity
    
    # If we still haven't found a perfect match, try one last configuration with a very strong magnet
    last_magnet = MagnetSpecs(
        diameter=magnet.diameter * 1.2,  # 20% larger
        length=magnet.length * 1.2,      # 20% longer
        magnetic_field=1.6,  # Very strong 1.6T
        material=magnet.material
    )
    
    # Try with the last configuration
    coil, velocity = optimize_coil_configuration(target_voltage, target_current, last_magnet)
    if coil is not None:
        return coil, velocity
    
    # If we still haven't found a perfect match, raise an error with detailed information
    raise ValueError(
        f"Could not find a configuration that meets target parameters:\n"
        f"Target Voltage: {target_voltage}V\n"
        f"Target Current: {target_current}A\n"
        f"Best achieved: {best_efficiency*100:.1f}% efficiency\n"
        f"Best configuration:\n"
        f"- Magnet: {best_magnet.diameter*1000:.1f}mm diameter, {best_magnet.length*1000:.1f}mm length, {best_magnet.magnetic_field:.1f}T\n"
        f"- Coil: {best_config.wire_diameter*1000:.1f}mm wire, {best_config.turns} turns\n"
        f"- Velocity: {best_velocity:.1f} m/s"
    )

def optimize_for_power(target_voltage: float, target_current: float, 
                       wire_diameter: float = None, pipe_thickness: float = None,
                       num_coils: int = None, coil_spacing: float = None,
                       magnet: MagnetSpecs = None,
                       connection: CoilConnection = None) -> SystemSpecs:
    """
    Optimize system parameters to meet target voltage and current requirements.
    Returns optimized system specifications.
    """
    # Set default coil spacing if not specified
    if coil_spacing is None:
        coil_spacing = 0.1  # Default 10% spacing between coils

    # Set default connection if not specified
    if connection is None:
        connection = CoilConnection(type="series", series_groups=1, parallel_coils=1)

    # If number of coils is specified, adjust other parameters accordingly
    if num_coils is not None:
        # Calculate required voltage and current per coil based on connection type
        voltage_per_coil = target_voltage / connection.calculate_total_voltage(1)
        current_per_coil = target_current / connection.calculate_total_current(1)
    else:
        num_coils = 5  # Default
        voltage_per_coil = target_voltage / connection.calculate_total_voltage(1)
        current_per_coil = target_current / connection.calculate_total_current(1)

    # Create default magnet if not provided
    if magnet is None:
        magnet = MagnetSpecs(
            material="N52",
            diameter=0.0254,  # 1 inch
            length=0.0254,    # 1 inch
            magnetic_field=1.4  # Tesla
        )

    # Calculate required coil area based on Faraday's law
    # V = N * B * A * v / L
    # For a given velocity, we need:
    # A = (V * L) / (N * B * v)
    
    # Start with a reasonable velocity
    velocity = 2.0  # m/s
    
    # Calculate minimum coil area needed
    min_coil_area = (voltage_per_coil * 0.2) / (1000 * magnet.magnetic_field * velocity)  # Assume 1000 turns initially
    
    # Calculate wire parameters
    if wire_diameter is None:
        # Calculate based on current density (4 A/mm²)
        wire_area = current_per_coil / 4e6  # m²
        wire_diameter = 2 * np.sqrt(wire_area / np.pi)
    
    # Calculate coil dimensions
    coil_inner_diameter = magnet.diameter + 0.002  # 2mm clearance
    coil_outer_diameter = coil_inner_diameter + 0.02  # 20mm winding thickness
    coil_length = magnet.length * 1.2  # 20% longer than magnet
    
    # Calculate required turns for target voltage
    coil_area = calculate_coil_area(coil_inner_diameter, coil_outer_diameter)
    required_turns = calculate_required_turns(voltage_per_coil, magnet.magnetic_field, coil_area, velocity, coil_length)
    
    # Create coil specification
    coil = CoilSpecs(
        inner_diameter=coil_inner_diameter,
        outer_diameter=coil_outer_diameter,
        length=coil_length * num_coils,  # Total length for all coils
        wire_diameter=wire_diameter,
        turns=required_turns * num_coils,  # Total turns for all coils
        material="Copper"
    )
    
    # Calculate tube dimensions
    if pipe_thickness is None:
        pipe_thickness = 0.004  # 4mm default
    
    tube = TubeSpecs(
        inner_diameter=coil_outer_diameter + 0.002,  # 2mm clearance
        length=coil_length * num_coils * (1 + coil_spacing),  # Add spacing between coils
        pipe_thickness=pipe_thickness,
        material="PVC"
    )
    
    # Create complete system
    system = SystemSpecs(
        magnet=magnet,
        coil=coil,
        tube=tube,
        velocity=velocity
    )
    
    # Fine-tune velocity to match target voltage exactly
    actual_voltage = calculate_induced_voltage(system)
    voltage_adjustment = target_voltage / actual_voltage
    system.velocity = velocity * voltage_adjustment
    
    return system

def calculate_component_weights(system: SystemSpecs) -> dict:
    """
    Calculate the weight of each component in the system.
    Returns weights in grams.
    """
    # Calculate magnet volume and weight
    magnet_volume = np.pi * (system.magnet.diameter/2)**2 * system.magnet.length
    magnet_weight = magnet_volume * NEODYMIUM_DENSITY * 1000  # Convert to grams
    
    # Calculate coil volume and weight
    coil_outer_volume = np.pi * (system.coil.outer_diameter/2)**2 * system.coil.length
    coil_inner_volume = np.pi * (system.coil.inner_diameter/2)**2 * system.coil.length
    coil_volume = coil_outer_volume - coil_inner_volume
    coil_weight = coil_volume * COPPER_DENSITY * 1000  # Convert to grams
    
    # Calculate tube volume and weight
    tube_outer_diameter = system.tube.inner_diameter + 2 * system.tube.pipe_thickness
    tube_outer_volume = np.pi * (tube_outer_diameter/2)**2 * system.tube.length
    tube_inner_volume = np.pi * (system.tube.inner_diameter/2)**2 * system.tube.length
    tube_volume = tube_outer_volume - tube_inner_volume
    tube_weight = tube_volume * PVC_DENSITY * 1000  # Convert to grams
    
    return {
        'magnet': magnet_weight,
        'coil': coil_weight,
        'tube': tube_weight,
        'total': magnet_weight + coil_weight + tube_weight
    }

def add_dimension_line(fig, x0, y0, x1, y1, label, orientation="horizontal", offset=15):
    """
    Add a dimension line with arrows and label.
    
    Args:
        fig: Plotly figure object
        x0, y0: Start point coordinates
        x1, y1: End point coordinates
        label: Dimension text
        orientation: "horizontal" or "vertical"
        offset: Offset distance for the dimension line
    """
    # Extension lines
    if orientation == "horizontal":
        # Vertical extension lines
        fig.add_shape(
            type="line",
            x0=x0, y0=y0,
            x1=x0, y1=y0 + offset,
            line=dict(color="black", width=1)
        )
        fig.add_shape(
            type="line",
            x0=x1, y0=y1,
            x1=x1, y1=y1 + offset,
            line=dict(color="black", width=1)
        )
        # Horizontal dimension line
        fig.add_shape(
            type="line",
            x0=x0, y0=y0 + offset,
            x1=x1, y1=y0 + offset,
            line=dict(color="black", width=1)
        )
        # Add label horizontally
        fig.add_annotation(
            x=(x0 + x1)/2,
            y=y0 + offset + 5,
            text=label,
            showarrow=False,
            font=dict(size=12),
            textangle=0
        )
    else:  # vertical
        # Horizontal extension lines
        fig.add_shape(
            type="line",
            x0=x0, y0=y0,
            x1=x0 + offset, y1=y0,
            line=dict(color="black", width=1)
        )
        fig.add_shape(
            type="line",
            x0=x1, y0=y1,
            x1=x1 + offset, y1=y1,
            line=dict(color="black", width=1)
        )
        # Vertical dimension line
        fig.add_shape(
            type="line",
            x0=x0 + offset, y0=y0,
            x1=x1 + offset, y1=y1,
            line=dict(color="black", width=1)
        )
        # Add label vertically
        fig.add_annotation(
            x=x0 + offset + 5,
            y=(y0 + y1)/2,
            text=label,
            showarrow=False,
            font=dict(size=12),
            textangle=90
        )

def create_2d_technical_drawing(system: SystemSpecs) -> go.Figure:
    """Create a technical drawing with properly aligned dimensions"""
    fig = go.Figure()
    
    # Extract dimensions
    tube_outer_radius = (system.tube.inner_diameter + 2 * system.tube.pipe_thickness) / 2
    tube_inner_radius = system.tube.inner_diameter / 2
    coil_outer_radius = system.coil.outer_diameter / 2
    magnet_radius = system.magnet.diameter / 2
    
    # Draw tube (outer rectangle)
    fig.add_shape(
        type="rect",
        x0=-tube_outer_radius,
        y0=0,
        x1=tube_outer_radius,
        y1=system.tube.length,
        line=dict(color="black", width=2),
        fillcolor="white"
    )
    
    # Draw tube inner space (inner rectangle)
    fig.add_shape(
        type="rect",
        x0=-tube_inner_radius,
        y0=0,
        x1=tube_inner_radius,
        y1=system.tube.length,
        line=dict(color="black", width=1),
        fillcolor="white"
    )
    
    # Draw coils
    num_coils = 5  # Example number of coils
    coil_length = system.coil.length / num_coils
    space_length = coil_length * 0.5
    
    for i in range(num_coils):
        y_start = i * (coil_length + space_length)
        fig.add_shape(
            type="rect",
            x0=-coil_outer_radius,
            y0=y_start,
            x1=coil_outer_radius,
            y1=y_start + coil_length,
            line=dict(color="black", width=1),
            fillcolor="orange",
            opacity=0.3
        )
    
    # Draw magnet assembly on the right
    magnet_x_offset = tube_outer_radius + 50  # 50mm offset from tube
    stick_length = system.tube.length * 0.8
    
    # Draw central stick
    fig.add_shape(
        type="line",
        x0=magnet_x_offset,
        y0=0,
        x1=magnet_x_offset,
        y1=stick_length,
        line=dict(color="black", width=2)
    )
    
    # Draw magnets
    num_magnets = 3
    magnet_spacing = stick_length / (num_magnets * 2)
    
    for i in range(num_magnets):
        magnet_y = (i * 2 + 1) * magnet_spacing
        fig.add_shape(
            type="rect",
            x0=magnet_x_offset - magnet_radius,
            y0=magnet_y - system.magnet.length/2,
            x1=magnet_x_offset + magnet_radius,
            y1=magnet_y + system.magnet.length/2,
            line=dict(color="black", width=1),
            fillcolor="grey",
            opacity=0.5
        )
    
    # Add dimensions
    # Tube outer diameter
    add_dimension_line(
        fig,
        -tube_outer_radius, -20,
        tube_outer_radius, -20,
        f"Pipe OD: {system.tube.inner_diameter*1000 + 2*system.tube.pipe_thickness*1000:.1f}mm",
        "horizontal"
    )
    
    # Tube inner diameter
    add_dimension_line(
        fig,
        -tube_inner_radius, -40,
        tube_inner_radius, -40,
        f"Pipe ID: {system.tube.inner_diameter*1000:.1f}mm",
        "horizontal"
    )
    
    # Tube length
    add_dimension_line(
        fig,
        tube_outer_radius + 20, 0,
        tube_outer_radius + 20, system.tube.length,
        f"Length: {system.tube.length*1000:.1f}mm",
        "vertical"
    )
    
    # Coil spacing
    if num_coils > 1:
        add_dimension_line(
            fig,
            -tube_outer_radius - 40, coil_length,
            -tube_outer_radius - 40, coil_length + space_length,
            f"Spacing: {space_length*1000:.1f}mm",
            "vertical"
        )
    
    # Update layout
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        width=800,
        height=600,
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            showticklabels=True,
            range=[-(tube_outer_radius + 100), magnet_x_offset + magnet_radius + 100]
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=True,
            showticklabels=True,
            scaleanchor="x",
            scaleratio=1,
            range=[-50, system.tube.length + 50]
        ),
        title="Technical Drawing (Side View)"
    )
    
    return fig 