# Temperature-Sensor-Simulation

## Project Overview
The **Temperature-Sensor-Simulation** project aims to create a cloud-based web application designed to assist cold chain companies in monitoring the transport conditions of their products. This is achieved through sensors installed in vehicles that periodically send data. Specifically, the application allows users to:

- Select a trailer and view a graph displaying temperature trends from the last 3 hours.
- Access a geographical map showing the current location of the trailer.
- Observe a table that indicates whether there are alarms triggered by temperatures exceeding the allowed maximum or by excessively long door open times.

## Project Components
- `main.py`: This file contains the Flask application responsible for running the server and exchanging data with the Google Cloud Platform Firestore database.
- `Sensors Directory`: Inside this folder, you'll find Python programs that simulate sensor data transmission. They use HTTP POST requests to send data to the server for analysis.
- `Static and templates Directories`: Inside these folders, you'll find HTML files used for the web interface. 
  
## Technologies Used
The project utilizes the following programming languages:
- Python
- HTML
- JavaScript
- CSS

---

## Getting Started

To set up and run this project locally, follow these steps:

1. Clone this repository to your local machine.
2. Install the necessary dependencies (requiremets.txt, app.yaml).
3. Configure your Google Cloud Platform service account.
4. Run the `main.py` file to start the Flask server.

---

## Contributions
For the basic structure of the website, I took inspiration from this [website](https://www.tutorialstonight.com/sample-html-code-for-homepage#google_vignette). 
Feel free to open issues, suggest improvements, or submit pull requests.

