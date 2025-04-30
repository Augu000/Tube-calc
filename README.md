# Electromagnetic Generator Calculator

This calculator helps design an electromagnetic generator system where a magnet moves through a coil to generate electricity based on Faraday's Law of Induction.

## Features

- Modern web interface with real-time calculations
- 3D visualization of the system components
- Detailed component specifications
- Performance metrics
- Human-readable recommendations
- Interactive parameter adjustment

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Web Interface
To run the web interface:
```bash
streamlit run app.py
```

The web interface will open in your default browser, where you can:
1. Enter your desired voltage and current
2. Click "Calculate" to see the results
3. View the 3D visualization of the system
4. See detailed specifications and recommendations

### Python Module
You can also use the calculator as a Python module:
```python
from electromagnetic_calculator.calculator import ElectromagneticCalculator

calculator = ElectromagneticCalculator()
results = calculator.calculate_system(target_voltage=12, target_current=2)
recommendations = calculator.get_recommendations()
```

## Input Parameters

- `target_voltage`: Desired output voltage in volts
- `target_current`: Desired output current in amperes

## Output

The calculator provides detailed specifications for:
- Magnet (size, material, magnetic field strength)
- Coil (dimensions, number of turns, wire specifications)
- Tube (dimensions, material)
- Performance metrics (velocity, actual voltage/current, power)

## Physics Behind the Calculator

The calculator uses Faraday's Law of Induction:
```
EMF = -N * dΦ/dt
```
where:
- EMF is the induced electromotive force (voltage)
- N is the number of turns in the coil
- dΦ/dt is the rate of change of magnetic flux

The magnetic flux Φ is calculated as:
```
Φ = B * A
```
where:
- B is the magnetic field strength
- A is the cross-sectional area of the magnet

## Future Improvements

- Add support for different magnet materials
- Include thermal calculations
- Add more detailed 3D visualization options
- Add export functionality for specifications
- Mobile application 