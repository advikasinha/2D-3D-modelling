Certainly! Here's a comprehensive `README.md` for the [2D-3D-modelling](https://github.com/advikasinha/2D-3D-modelling) repository:

---

# 2D-3D Modelling

This project facilitates the conversion of 2D engineering sketches into 3D models. It leverages OpenCV for shape recognition, utilizes tries and graphs for entity relationships, and employs SOLIDWORKS with VBA scripts for 3D modelling. Developed as part of the TEB (MIT-101) coursework under the MEID Department at IIT Roorkee.([GitHub][1])

## Features

* **Shape Detection**: Utilizes OpenCV to identify basic geometric shapes (e.g., rectangles, squares) from 2D sketches.
* **Dimension Extraction**: Extracts dimensions from identified shapes to inform 3D modelling.
* **Entity Relationship Mapping**: Employs tries and graphs to map relationships between different entities in the sketch.
* **3D Modelling**: Generates 3D models using SOLIDWORKS via VBA scripting based on the extracted data.
* **Interactive User Input**: Prompts users to specify whether the shape is simple or complex, adjusting the processing accordingly.

## Prerequisites

* **Python 3.x**
* **OpenCV**: For image processing and shape detection.
* **SOLIDWORKS**: For 3D modelling.
* **VBA Support**: Enabled in SOLIDWORKS for script execution.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/advikasinha/2D-3D-modelling.git
   cd 2D-3D-modelling
   ```



2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```



## Usage

1. **Prepare Your 2D Sketch**:
   Ensure your 2D sketch is in a compatible image format (e.g., PNG, JPEG) and placed in the appropriate directory.

2. **Run the Script**:

   ```bash
   python codev1.py
   ```



3. **Follow Prompts**:
   The script will prompt you to specify the type of shape:

   * Enter `1` for a simple shape.
   * Enter `2` for a complex shape (e.g., a rectangle containing a square).

4. **Output**:
   The script will process the image, extract dimensions, and generate a 3D model in SOLIDWORKS using VBA scripting.

## Project Structure

* **`codev1.py`**: Main script for processing and 3D model generation.
* **`cv_scripts/`**: Contains OpenCV-related scripts for image processing.
* **`cube-cuboid-scrips/`**: VBA scripts for generating cube and cuboid models in SOLIDWORKS.
* **`stacking/`**: Scripts related to stacking multiple shapes or components.
* **`id_dimension_extraction.py`**: Script for extracting dimensions from identified shapes.
* **`openCV_detection_demo.webm`**: Demo video showcasing OpenCV detection capabilities.
* **`requirements.txt`**: List of Python dependencies.
* **`server.py`**: Script to set up a local server for interfacing with SOLIDWORKS.([GitHub][2], [GitHub][1])

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Developed as part of the TEB (MIT-101) coursework under the MEID Department at IIT Roorkee.

---

Feel free to customize this `README.md` further to suit your project's specific needs.

[1]: https://github.com/topics/2d-to-3d?utm_source=chatgpt.com "2d-to-3d · GitHub Topics · GitHub"
[2]: https://github.com/Developer-Kim/2D-to-3D-Modeling-using-AI?utm_source=chatgpt.com "Developer-Kim/2D-to-3D-Modeling-using-AI - GitHub"
