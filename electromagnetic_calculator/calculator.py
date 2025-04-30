from typing import Dict, Any
import numpy as np
from .physics import (
    SystemSpecs, MagnetSpecs, CoilSpecs, TubeSpecs,
    calculate_induced_voltage, calculate_induced_current,
    calculate_power, optimize_for_power, calculate_component_weights,
    calculate_coil_resistance
)

class ElectromagneticCalculator:
    """Main calculator class for electromagnetic system design"""
    
    def __init__(self):
        self.system: SystemSpecs = None
    
    def calculate_system(self, target_voltage: float, target_current: float, 
                        wire_diameter: float = None, pipe_thickness: float = None,
                        num_coils: int = 5, coil_spacing: float = 0.5,
                        magnet_specs: dict = None) -> Dict[str, Any]:
        """
        Calculate the optimal system parameters for given target voltage and current
        
        Args:
            target_voltage: Desired output voltage in volts
            target_current: Desired output current in amperes
            wire_diameter: Optional wire diameter in meters
            pipe_thickness: Optional pipe wall thickness in meters
            num_coils: Number of coil sections (default: 5)
            coil_spacing: Space between coils as a factor of coil length (default: 0.5)
            magnet_specs: Dictionary containing magnet specifications:
                         - material: Type of magnet
                         - diameter: Diameter in meters
                         - length: Length in meters
                         - magnetic_field: Field strength in Tesla
        """
        # Use provided magnet specs or defaults
        if magnet_specs is None:
            magnet = MagnetSpecs(
                diameter=0.012,  # 12mm
                length=0.05,     # 50mm
                magnetic_field=1.2,  # Tesla
                material="N52 Neodymium"
            )
        else:
            magnet = MagnetSpecs(
                diameter=magnet_specs['diameter'],
                length=magnet_specs['length'],
                magnetic_field=magnet_specs['magnetic_field'],
                material=magnet_specs['material']
            )

        self.system = optimize_for_power(
            target_voltage=target_voltage,
            target_current=target_current,
            wire_diameter=wire_diameter,
            pipe_thickness=pipe_thickness,
            num_coils=num_coils,
            coil_spacing=coil_spacing,
            magnet=magnet
        )
        
        # Calculate actual performance
        actual_voltage = calculate_induced_voltage(self.system)
        actual_current = calculate_induced_current(self.system)
        power = calculate_power(self.system)
        
        # Calculate magnetic flux
        magnet_area = np.pi * (self.system.magnet.diameter/2)**2
        magnetic_flux = self.system.magnet.magnetic_field * magnet_area
        
        return {
            "magnet": {
                "diameter": self.system.magnet.diameter * 1000,  # mm
                "length": self.system.magnet.length * 1000,  # mm
                "magnetic_field": self.system.magnet.magnetic_field,  # T
                "material": self.system.magnet.material
            },
            "coil": {
                "inner_diameter": self.system.coil.inner_diameter * 1000,  # mm
                "outer_diameter": self.system.coil.outer_diameter * 1000,  # mm
                "length": self.system.coil.length * 1000,  # mm
                "wire_diameter": self.system.coil.wire_diameter * 1000,  # mm
                "turns": self.system.coil.turns,
                "material": self.system.coil.material,
                "resistance": calculate_coil_resistance(self.system.coil),  # Ω
                "num_sections": num_coils,
                "spacing": coil_spacing
            },
            "tube": {
                "inner_diameter": self.system.tube.inner_diameter * 1000,  # mm
                "length": self.system.tube.length * 1000,  # mm
                "material": self.system.tube.material
            },
            "performance": {
                "velocity": self.system.velocity,  # m/s
                "voltage": actual_voltage,  # V
                "current": actual_current,  # A
                "power": power,  # W
                "magnetic_flux": magnetic_flux  # Weber (Wb)
            }
        }
    
    def get_recommendations(self) -> Dict[str, str]:
        """
        Get human-readable recommendations based on the calculated system
        """
        if not self.system:
            return {"error": "No system calculated yet"}
        
        recommendations = {
            "magnet": f"Use a {self.system.magnet.material} magnet with diameter {self.system.magnet.diameter*1000:.1f}mm "
                     f"and length {self.system.magnet.length*1000:.1f}mm",
            "coil": f"Wind {self.system.coil.turns} turns of {self.system.coil.wire_diameter*1000:.1f}mm diameter "
                   f"{self.system.coil.material} wire around a {self.system.coil.inner_diameter*1000:.1f}mm diameter form",
            "tube": f"Use a {self.system.tube.material} tube with inner diameter {self.system.tube.inner_diameter*1000:.1f}mm "
                   f"and length {self.system.tube.length*1000:.1f}mm",
            "operation": f"Move the magnet at approximately {self.system.velocity:.1f} m/s through the coil"
        }
        
        return recommendations
    
    def calculate_component_weights(self, results: dict) -> dict:
        """
        Calculate the weight of each component in the system.
        Returns weights in grams.
        """
        # Convert dimensions back to meters for calculations
        magnet = MagnetSpecs(
            diameter=results['magnet']['diameter'] / 1000,
            length=results['magnet']['length'] / 1000,
            magnetic_field=results['magnet']['magnetic_field'],
            material=results['magnet']['material']
        )
        
        coil = CoilSpecs(
            inner_diameter=results['coil']['inner_diameter'] / 1000,
            outer_diameter=results['coil']['outer_diameter'] / 1000,
            length=results['coil']['length'] / 1000,
            wire_diameter=results['coil']['wire_diameter'] / 1000,
            turns=results['coil']['turns'],
            material=results['coil']['material']
        )
        
        tube = TubeSpecs(
            inner_diameter=results['tube']['inner_diameter'] / 1000,
            length=results['tube']['length'] / 1000,
            material=results['tube']['material']
        )
        
        system = SystemSpecs(
            magnet=magnet,
            coil=coil,
            tube=tube,
            velocity=results['performance']['velocity']
        )
        
        return calculate_component_weights(system)

def main():
    # Example usage
    calculator = ElectromagneticCalculator()
    results = calculator.calculate_system(target_voltage=12, target_current=2)
    recommendations = calculator.get_recommendations()
    
    print("\nSystem Specifications:")
    for category, specs in results.items():
        print(f"\n{category.upper()}:")
        for param, value in specs.items():
            print(f"  {param}: {value}")
    
    print("\nRecommendations:")
    for category, recommendation in recommendations.items():
        print(f"\n{category}: {recommendation}")

if __name__ == "__main__":
    main() 