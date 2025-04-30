import streamlit as st
import plotly.graph_objects as go
import numpy as np
from electromagnetic_calculator import ElectromagneticCalculator

# Set page config
st.set_page_config(
    page_title="Electromagnetic Generator Calculator",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .result-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-box {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def create_cylinder_mesh(radius, height, center=(0, 0, 0), color='blue', opacity=0.5):
    """Create a cylinder mesh using mesh3d"""
    theta = np.linspace(0, 2*np.pi, 20)
    z = np.linspace(0, height, 2)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x = radius * np.cos(theta_grid) + center[0]
    y = radius * np.sin(theta_grid) + center[1]
    z = z_grid + center[2]
    
    return go.Mesh3d(
        x=x.flatten(),
        y=y.flatten(),
        z=z.flatten(),
        color=color,
        opacity=opacity,
        flatshading=True
    )

def create_3d_view(tube, coil, magnet, pipe_thickness):
    """Create a 3D visualization of the system"""
    fig = go.Figure()
    
    # Create cylinder points
    def create_cylinder_mesh(r, h, x0=0, y0=0, z0=0, color='gray', name=''):
        theta = np.linspace(0, 2*np.pi, 30)
        z = np.linspace(z0, z0 + h, 2)
        theta_grid, z_grid = np.meshgrid(theta, z)
        
        x_grid = r * np.cos(theta_grid) + x0
        y_grid = r * np.sin(theta_grid) + y0
        
        return go.Surface(
            x=x_grid,
            y=y_grid,
            z=z_grid,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            opacity=0.7,
            name=name,
            hoverinfo='name+text',
            hovertext=f'Diameter: {2*r:.1f}mm<br>Height: {h:.1f}mm'
        )
    
    # Add tube (transparent)
    tube_outer_diameter = tube['inner_diameter'] + 2 * pipe_thickness
    fig.add_trace(create_cylinder_mesh(
        tube_outer_diameter/2, 
        tube['length'],
        color='lightgray',
        name=f'Tube (Wall: {pipe_thickness:.1f}mm)'
    ))
    
    # Add coils (as segments)
    num_coils = 5
    coil_length = coil['length'] / num_coils
    space_length = coil_length * 0.5
    
    for i in range(num_coils):
        z_pos = i * (coil_length + space_length)
        fig.add_trace(create_cylinder_mesh(
            coil['outer_diameter']/2,
            coil_length,
            z0=z_pos,
            color='saddlebrown',
            name=f'Coil (Wire: {coil["wire_diameter"]:.1f}mm)'
        ))
    
    # Add magnet stick with magnets
    stick_length = tube['length'] * 0.8
    stick_diameter = magnet['diameter'] * 0.3
    num_magnets = 3
    magnet_spacing = stick_length / (num_magnets * 2)
    
    # Add stick
    fig.add_trace(create_cylinder_mesh(
        stick_diameter/2,
        stick_length,
        color='silver',
        name='Stick'
    ))
    
    # Add magnets
    for i in range(num_magnets):
        z_pos = (i * 2 + 1) * magnet_spacing
        fig.add_trace(create_cylinder_mesh(
            magnet['diameter']/2,
            magnet['length'],
            z0=z_pos,
            color='crimson',
            name='Magnet'
        ))
    
    # Update layout
    fig.update_layout(
        scene=dict(
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1)
            ),
            aspectmode='data',
            xaxis_title='X (mm)',
            yaxis_title='Y (mm)',
            zaxis_title='Z (mm)'
        ),
        showlegend=True,
        title='3D System View',
        height=600
    )
    
    return fig

def create_2d_projection(tube, coil, magnet, pipe_thickness):
    """Create a simplified technical drawing with clear dimensions"""
    fig = go.Figure()
    
    # Calculate dimensions
    tube_outer_diameter = tube['inner_diameter'] + 2 * pipe_thickness
    tube_outer_radius = tube_outer_diameter / 2
    tube_inner_radius = tube['inner_diameter'] / 2
    
    # Add pipe (main rectangle)
    fig.add_shape(
        type="rect",
        x0=-tube_outer_radius,
        y0=0,
        x1=tube_outer_radius,
        y1=tube['length'],
        line=dict(color="black", width=2),
        fillcolor="white"
    )
    
    # Add coils as orange rectangles
    num_coils = 5
    coil_length = coil['length'] / num_coils
    space_length = coil_length * 0.5
    coil_outer_radius = coil['outer_diameter'] / 2
    
    for i in range(num_coils):
        y_start = i * (coil_length + space_length)
        
        # Coil rectangle
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
    
    # Add magnet stick and magnets (to the right of pipe)
    stick_x_offset = tube_outer_radius + 50  # Move stick to the right
    stick_length = tube['length'] * 0.8
    num_magnets = 3
    magnet_spacing = stick_length / (num_magnets * 2)
    
    # Add stick (vertical line)
    fig.add_shape(
        type="line",
        x0=stick_x_offset,
        y0=0,
        x1=stick_x_offset,
        y1=stick_length,
        line=dict(color="black", width=2)
    )
    
    # Add magnets (grey rectangles)
    magnet_width = magnet['diameter']
    for i in range(num_magnets):
        magnet_y = (i * 2 + 1) * magnet_spacing
        
        fig.add_shape(
            type="rect",
            x0=stick_x_offset - magnet_width/2,
            y0=magnet_y - magnet['length']/2,
            x1=stick_x_offset + magnet_width/2,
            y1=magnet_y + magnet['length']/2,
            line=dict(color="black", width=1),
            fillcolor="grey",
            opacity=0.5
        )
    
    # Add dimensions
    def add_dimension(x0, x1, y, label, direction="horizontal"):
        arrow_size = 5
        extension_length = 15
        
        if direction == "horizontal":
            if x1 is None:
                return
            # Extension lines
            fig.add_shape(type="line", x0=x0, y0=y, x1=x0, y1=y+extension_length, line=dict(color="black", width=1))
            fig.add_shape(type="line", x0=x1, y0=y, x1=x1, y1=y+extension_length, line=dict(color="black", width=1))
            
            # Dimension line with arrows
            fig.add_shape(type="line", x0=x0, y0=y+extension_length, x1=x1, y1=y+extension_length, 
                         line=dict(color="black", width=1))
            
            # Label
            fig.add_annotation(x=(x0+x1)/2, y=y+extension_length+10, text=label, showarrow=False, 
                             font=dict(size=14, color="black"))
        else:  # vertical
            if y is None:
                return
            # Extension lines
            fig.add_shape(type="line", x0=x0, y0=0, x1=x0+extension_length, y1=0, line=dict(color="black", width=1))
            fig.add_shape(type="line", x0=x0, y0=tube['length'], x1=x0+extension_length, y1=tube['length'], 
                         line=dict(color="black", width=1))
            
            # Dimension line with arrows
            fig.add_shape(type="line", x0=x0+extension_length, y0=0, x1=x0+extension_length, y1=tube['length'], 
                         line=dict(color="black", width=1))
            
            # Label
            fig.add_annotation(x=x0+extension_length+10, y=tube['length']/2, text=label, showarrow=False, 
                             font=dict(size=14, color="black"))
    
    # Add pipe dimensions
    add_dimension(-tube_outer_radius, tube_outer_radius, -30, f"Pipe OD: {tube_outer_diameter:.1f}mm")
    add_dimension(-tube_inner_radius, tube_inner_radius, -60, f"Pipe ID: {tube['inner_diameter']:.1f}mm")
    add_dimension(tube_outer_radius+10, None, 0, f"Length: {tube['length']:.1f}mm", "vertical")
    
    # Add coil dimensions
    first_coil_start = 0
    first_coil_end = coil_length
    add_dimension(-coil_outer_radius-30, None, first_coil_start, f"Coil: {coil_length:.1f}mm", "vertical")
    add_dimension(-coil_outer_radius-60, None, first_coil_end, f"Space: {space_length:.1f}mm", "vertical")
    
    # Add magnet dimensions
    first_magnet_y = magnet_spacing
    add_dimension(stick_x_offset-magnet_width/2, stick_x_offset+magnet_width/2, -30, 
                 f"Magnet: {magnet['diameter']:.1f}mm")
    add_dimension(stick_x_offset+magnet_width/2+10, None, 0, f"Magnet spacing: {magnet_spacing*2:.1f}mm", "vertical")
    
    # Update layout
    fig.update_layout(
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-tube_outer_radius-100, stick_x_offset+100]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=20, b=20),
        height=800,
        title='Technical Drawing'
    )
    
    return fig

# Title and description
st.title("⚡ Electromagnetic Generator Calculator")
st.markdown("""
This calculator helps you design an electromagnetic generator system where a magnet moves through a coil to generate electricity.
Enter your desired voltage and current, and the calculator will provide all the necessary specifications.
""")

# Create main layout with two columns
main_col1, main_col2 = st.columns([1, 1])

# Left column for input parameters
with main_col1:
    st.header("Input Parameters")
    
    # Target output parameters
    st.subheader("Target Output")
    target_col1, target_col2 = st.columns(2)
    with target_col1:
        target_voltage = st.number_input(
            "Desired Voltage (V)",
            min_value=0.1,
            max_value=1000.0,
            value=12.0,
            step=0.1,
            help="The voltage you want to generate"
        )

    with target_col2:
        target_current = st.number_input(
            "Desired Current (A)",
            min_value=0.1,
            max_value=100.0,
            value=2.0,
            step=0.1,
            help="The current you want to generate"
        )

    # Wire parameters
    st.subheader("Wire Specifications")
    wire_col1, wire_col2 = st.columns(2)
    with wire_col1:
        wire_diameter = st.number_input(
            "Wire Diameter (mm)",
            min_value=0.1,
            max_value=5.0,
            value=1.0,
            step=0.1,
            help="The diameter of the copper wire"
        )
        wire_material = st.selectbox(
            "Wire Material",
            options=["Copper"],
            help="Material of the wire (currently only copper is supported)"
        )

    # Coil parameters
    st.subheader("Coil Configuration")
    coil_col1, coil_col2 = st.columns(2)
    with coil_col1:
        num_coils = st.number_input(
            "Number of Coils",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="Number of coil sections in the generator"
        )
    with coil_col2:
        coil_spacing = st.number_input(
            "Coil Spacing Factor",
            min_value=0.1,
            max_value=2.0,
            value=0.5,
            step=0.1,
            help="Space between coils as a factor of coil length (0.5 means half coil length)"
        )

    # Magnet parameters
    st.subheader("Magnet Specifications")
    mag_col1, mag_col2 = st.columns(2)
    with mag_col1:
        magnet_material = st.selectbox(
            "Magnet Material",
            options=["N52 Neodymium", "N42 Neodymium", "N35 Neodymium"],
            help="Type of permanent magnet"
        )
        magnet_diameter = st.number_input(
            "Magnet Diameter (mm)",
            min_value=1.0,
            max_value=50.0,
            value=12.0,
            step=1.0,
            help="Diameter of the magnet"
        )
    with mag_col2:
        magnet_length = st.number_input(
            "Magnet Length (mm)",
            min_value=1.0,
            max_value=100.0,
            value=50.0,
            step=1.0,
            help="Length of the magnet"
        )
        magnetic_field = st.number_input(
            "Magnetic Field (Tesla)",
            min_value=0.1,
            max_value=2.0,
            value=1.2,
            step=0.1,
            help="Magnetic field strength of the magnet"
        )

    # Tube parameters
    st.subheader("Tube Specifications")
    tube_col1, tube_col2 = st.columns(2)
    with tube_col1:
        pipe_thickness = st.number_input(
            "Pipe Wall Thickness (mm)",
            min_value=0.5,
            max_value=10.0,
            value=2.0,
            step=0.5,
            help="The thickness of the PVC pipe wall"
        )
        tube_material = st.selectbox(
            "Tube Material",
            options=["PVC"],
            help="Material of the tube (currently only PVC is supported)"
        )

    # Calculate button
    if st.button("Calculate", type="primary"):
        calculator = ElectromagneticCalculator()
        results = calculator.calculate_system(
            target_voltage=target_voltage,
            target_current=target_current,
            wire_diameter=wire_diameter/1000,  # Convert to meters
            pipe_thickness=pipe_thickness/1000,  # Convert to meters
            num_coils=num_coils,
            coil_spacing=coil_spacing,
            magnet_specs={
                "material": magnet_material,
                "diameter": magnet_diameter/1000,  # Convert to meters
                "length": magnet_length/1000,  # Convert to meters
                "magnetic_field": magnetic_field
            }
        )
        recommendations = calculator.get_recommendations()
        weights = calculator.calculate_component_weights(results)
        
        # Store results in session state
        st.session_state.results = results
        st.session_state.recommendations = recommendations
        st.session_state.weights = weights

# Right column for visualization
with main_col2:
    st.header("System Visualization")
    if 'results' in st.session_state:
        tab1, tab2 = st.tabs(["3D View", "2D View"])
        
        with tab1:
            fig_3d = create_3d_view(
                st.session_state.results['tube'],
                st.session_state.results['coil'],
                st.session_state.results['magnet'],
                pipe_thickness
            )
            st.plotly_chart(fig_3d, use_container_width=True)
        
        with tab2:
            fig_2d = create_2d_projection(
                st.session_state.results['tube'],
                st.session_state.results['coil'],
                st.session_state.results['magnet'],
                pipe_thickness
            )
            st.plotly_chart(fig_2d, use_container_width=True)

# Results section (full width)
if 'results' in st.session_state:
    # Main performance metrics in large boxes at the top
    st.header("Generator Output")
    perf_col1, perf_col2, perf_col3 = st.columns(3)
    
    with perf_col1:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ffffff;'>
            <h3 style='margin: 0; color: #ff9800;'>Voltage</h3>
            <h2 style='color: #ffffff; margin: 10px 0;'>{:.1f} V</h2>
            <p style='margin: 0; color: #888;'>Target: {:.1f} V</p>
        </div>
        """.format(st.session_state.results['performance']['voltage'], target_voltage), unsafe_allow_html=True)
    
    with perf_col2:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ffffff;'>
            <h3 style='margin: 0; color: #ff9800;'>Current</h3>
            <h2 style='color: #ffffff; margin: 10px 0;'>{:.2f} A</h2>
            <p style='margin: 0; color: #888;'>Target: {:.1f} A</p>
        </div>
        """.format(st.session_state.results['performance']['current'], target_current), unsafe_allow_html=True)
    
    with perf_col3:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ffffff;'>
            <h3 style='margin: 0; color: #ff9800;'>Power</h3>
            <h2 style='color: #ffffff; margin: 10px 0;'>{:.2f} W</h2>
            <p style='margin: 0; color: #888;'>Efficiency: {:.1f}%</p>
        </div>
        """.format(st.session_state.results['performance']['power'], 
                  (st.session_state.results['performance']['power']/(target_voltage*target_current))*100), 
                  unsafe_allow_html=True)

    # Component specifications in a clean layout
    st.header("Component Specifications")
    specs_col1, specs_col2, specs_col3 = st.columns(3)
    
    with specs_col1:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #ffffff;'>
            <h3 style='color: #ff9800;'>🧲 Magnet</h3>
            <ul style='list-style-type: none; padding: 0; color: #ffffff;'>
                <li>Diameter: {:.1f} mm</li>
                <li>Length: {:.1f} mm</li>
                <li>Field Strength: {:.2f} T</li>
                <li>Weight: {:.1f} g</li>
                <li>Material: {}</li>
            </ul>
        </div>
        """.format(
            st.session_state.results['magnet']['diameter'],
            st.session_state.results['magnet']['length'],
            st.session_state.results['magnet']['magnetic_field'],
            st.session_state.weights['magnet'],
            st.session_state.results['magnet']['material']
        ), unsafe_allow_html=True)
    
    with specs_col2:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #ffffff;'>
            <h3 style='color: #ff9800;'>🔄 Coil</h3>
            <ul style='list-style-type: none; padding: 0; color: #ffffff;'>
                <li>Turns: {:,}</li>
                <li>Wire Diameter: {:.2f} mm</li>
                <li>Inner Diameter: {:.1f} mm</li>
                <li>Outer Diameter: {:.1f} mm</li>
                <li>Length: {:.1f} mm</li>
                <li>Weight: {:.1f} g</li>
            </ul>
        </div>
        """.format(
            st.session_state.results['coil']['turns'],
            st.session_state.results['coil']['wire_diameter'],
            st.session_state.results['coil']['inner_diameter'],
            st.session_state.results['coil']['outer_diameter'],
            st.session_state.results['coil']['length'],
            st.session_state.weights['coil']
        ), unsafe_allow_html=True)
    
    with specs_col3:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #ffffff;'>
            <h3 style='color: #ff9800;'>📏 Tube</h3>
            <ul style='list-style-type: none; padding: 0; color: #ffffff;'>
                <li>Inner Diameter: {:.1f} mm</li>
                <li>Wall Thickness: {:.1f} mm</li>
                <li>Length: {:.1f} mm</li>
                <li>Weight: {:.1f} g</li>
                <li>Material: {}</li>
            </ul>
        </div>
        """.format(
            st.session_state.results['tube']['inner_diameter'],
            pipe_thickness,
            st.session_state.results['tube']['length'],
            st.session_state.weights['tube'],
            st.session_state.results['tube']['material']
        ), unsafe_allow_html=True)

    # Physics calculations in a detailed box
    st.header("Physics Analysis")
    phys_col1, phys_col2 = st.columns(2)
    
    with phys_col1:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #ffffff;'>
            <h3 style='color: #ff9800;'>Magnetic Properties</h3>
            <ul style='list-style-type: none; padding: 0; color: #ffffff;'>
                <li>Field Strength: {:.2f} Tesla</li>
                <li>Magnetic Flux: {:.2e} Weber</li>
                <li>Required Velocity: {:.2f} m/s</li>
            </ul>
        </div>
        """.format(
            st.session_state.results['magnet']['magnetic_field'],
            st.session_state.results['performance']['magnetic_flux'],
            st.session_state.results['performance']['velocity']
        ), unsafe_allow_html=True)
    
    with phys_col2:
        st.markdown("""
        <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #ffffff;'>
            <h3 style='color: #ff9800;'>Electrical Properties</h3>
            <ul style='list-style-type: none; padding: 0; color: #ffffff;'>
                <li>Coil Resistance: {:.2f} Ω</li>
                <li>Voltage/Turn: {:.3f} V/turn</li>
                <li>Current Density: {:.2f} A/mm²</li>
                <li>Power Density: {:.2f} W/kg</li>
            </ul>
        </div>
        """.format(
            st.session_state.results['coil']['resistance'],
            st.session_state.results['performance']['voltage']/st.session_state.results['coil']['turns'],
            st.session_state.results['performance']['current']/(np.pi*(st.session_state.results['coil']['wire_diameter']/2000)**2),
            st.session_state.results['performance']['power']/st.session_state.weights['total']*1000
        ), unsafe_allow_html=True)

    # Operation instructions
    st.header("Operation Instructions")
    st.markdown("""
    <div style='background-color: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #ffffff;'>
        <h3 style='color: #ff9800; margin-top: 0;'>How to Use</h3>
        <p style='color: #ffffff;'>{}</p>
        <p style='color: #ffffff;'>{}</p>
        <p style='color: #ffffff;'>{}</p>
        <p style='color: #ffffff;'>{}</p>
    </div>
    """.format(
        st.session_state.recommendations['magnet'],
        st.session_state.recommendations['coil'],
        st.session_state.recommendations['tube'],
        st.session_state.recommendations['operation']
    ), unsafe_allow_html=True) 