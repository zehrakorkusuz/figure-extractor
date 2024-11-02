import os
import subprocess
import logging
from flask import Flask, request, jsonify
from typing import Dict, List
import time
import json
import uuid
import requests

app = Flask(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class PDFProcessor: #changed path to mounted folder
    def __init__(self, output_dir: str = "/pdffigures2/data/output", jar_path: str = "/pdffigures2/pdffigures2.jar"):
        self.output_dir = os.path.abspath(output_dir) + '/'  # Ensure trailing slash
        self.jar_path = jar_path
        os.makedirs(self.output_dir, exist_ok=True)
        logging.info(f"Initialized PDFProcessor with output_dir: {self.output_dir}")
        logging.info(f"JAR path: {self.jar_path}")
        # Create output directories if they do not exist 
        self.figure_output_dir = os.path.join(self.output_dir, "figures/")
        self.metadata_output_dir = os.path.join(self.output_dir, "metadata/")
        os.makedirs(self.figure_output_dir, exist_ok=True)
        os.makedirs(self.metadata_output_dir, exist_ok=True)


    def download_pdf(self, url: str) -> str:
        """Download a PDF from a URL and save it locally."""
        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise ValueError(f"Failed to download PDF from URL. Status code: {response.status_code}")

            # Generate a unique filename for the downloaded PDF
            pdf_name = f"{uuid.uuid4()}.pdf"
            pdf_path = os.path.join(self.output_dir, pdf_name)
            with open(pdf_path, "wb") as pdf_file:
                pdf_file.write(response.content)

            logging.info(f"Downloaded PDF from {url} to {pdf_path}")
            return pdf_path

        except Exception as e:
            error_msg = f"Error downloading PDF: {str(e)}"
            logging.error(error_msg)
            return ""


    def validate_pdf_path(self, pdf_path: str) -> tuple[bool, str]:
        expanded_path = os.path.expanduser(pdf_path)
        abs_path = os.path.abspath(expanded_path)
        logging.debug(f"Validating PDF path: {abs_path}")
        
        if not os.path.exists(abs_path):
            return False, f"Path does not exist: {abs_path}"
        if not os.path.isfile(abs_path):
            return False, f"Path is not a file: {abs_path}"
        if not abs_path.lower().endswith('.pdf'):
            return False, f"File is not a PDF: {abs_path}"
        if not os.access(abs_path, os.R_OK):
            return False, f"File is not readable: {abs_path}"
        
        return True, abs_path

    def process_single_pdf(self, pdf_path: str, dpi: str = "300", visualization: bool = False) -> dict:
        try:
            # Validate PDF path
            is_valid, path_or_error = self.validate_pdf_path(pdf_path)
            if not is_valid:
                logging.error(path_or_error)
                return {"success": False, "error": path_or_error}

            pdf_path = path_or_error  # Use validated absolute path

            base_command = [
                "java", "-jar", self.jar_path,
                pdf_path,
                "-m", self.metadata_output_dir,
                "-d", self.figure_output_dir,
                "--dpi", dpi
            ]

            if visualization:
                base_command.append("-r")  # Add visualization flag if required

            logging.info(f"Executing command: {' '.join(base_command)}")
            result = subprocess.run(base_command, capture_output=True, text=True)

            # Log command output for debugging
            logging.debug(f"Command stdout: {result.stdout}")
            logging.debug(f"Command stderr: {result.stderr}")

            if result.returncode != 0:
                error_msg = f"Command failed with return code {result.returncode}: {result.stderr}"
                logging.error(error_msg)
                return {"success": False, "error": error_msg}

            # Check for the generated figures
            figures_output = [
                f for f in os.listdir(self.output_dir)
                if f.startswith(os.path.basename(pdf_path).replace('.pdf', '')) and f.endswith('.png')
            ]

            if not figures_output:
                error_msg = "No figures were generated."
                logging.error(error_msg)
                return {"success": False, "error": error_msg}

            # Check for the metadata file
            metadata_file = os.path.join(self.output_dir, f"{os.path.basename(pdf_path).replace('.pdf', '')}.json")
            metadata_content = {}
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as mf:
                    metadata_content = json.load(mf)
            else:
                logging.warning(f"Metadata file not found: {metadata_file}")

            # Extract figure information from metadata if it exists
            total_figures = len(figures_output)  # Count the total number of figures

            # Summarize metadata to include only relevant fields
            summarized_metadata = []
            if metadata_content:
                summarized_metadata = [
                    {
                        "name": item.get("name"),
                        "caption": item.get("caption"),
                        "renderURL": item.get("renderURL"),
                    }
                    for item in metadata_content
                ]

            # Return the list of figures that were generated, total count, and the metadata
            return {
                "success": True,
                "totalFigures": total_figures,
                "figures": figures_output,
                "metadata": summarized_metadata,
                "message": "Figures extracted successfully."
            }

        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}

    def visualize_pdf(self, pdf_path: str, intermediate_steps: bool = False) -> Dict:
        """Visualize how the PDF was parsed using the Scala app."""
        try:
            # Validate PDF path
            is_valid, path_or_error = self.validate_pdf_path(pdf_path)
            if not is_valid:
                logging.error(path_or_error)
                return {"success": False, "error": path_or_error}
            
            pdf_path = path_or_error  # Use validated absolute path

            # Base command for visualization
            command = [
                "sbt", "runMain", "org.allenai.pdffigures2.FigureExtractorVisualizationCli", pdf_path
            ]
            if intermediate_steps:
                command.append("-s")  # Add flag for intermediate steps if needed
            
            logging.info(f"Executing visualization command: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True)

            # Log command output for debugging
            logging.debug(f"Visualization command stdout: {result.stdout}")
            logging.debug(f"Visualization command stderr: {result.stderr}")

            if result.returncode != 0:
                error_msg = f"Visualization command failed with return code {result.returncode}: {result.stderr}"
                logging.error(error_msg)
                return {"success": False, "error": error_msg}

            return {
                "success": True,
                "message": "Visualization completed successfully.",
                "output": result.stdout
            }

        except Exception as e:
            error_msg = f"Error visualizing PDF: {str(e)}"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}

    def process_directory(self, pdf_directory: str, stat_file: str) -> dict:
        """Process multiple PDFs in a directory."""
        try:
            if not os.path.exists(pdf_directory):
                logging.error("PDF directory does not exist.")
                return {"success": False, "error": "Invalid PDF directory path."}

            # Create output directories if they do not exist
            figure_output_dir = os.path.join(self.output_dir, "figures/")
            metadata_output_dir = os.path.join(self.output_dir, "metadata/")
            os.makedirs(figure_output_dir, exist_ok=True)
            os.makedirs(metadata_output_dir, exist_ok=True)

            # Ensure the command is properly formatted
            base_command = (
                f'sbt "runMain org.allenai.pdffigures2.FigureExtractorBatchCli '
                f'{pdf_directory} -s {stat_file} -m {figure_output_dir} -d {metadata_output_dir}"'
            )

            logging.info(f"Executing batch command: {base_command}")
            result = subprocess.run(base_command, shell=True, capture_output=True, text=True, cwd="/pdffigures2")

            # Log command output for debugging
            logging.debug(f"Batch command stdout: {result.stdout}")
            logging.debug(f"Batch command stderr: {result.stderr}")

            if result.returncode != 0:
                error_msg = f"Batch command failed with return code {result.returncode}: {result.stderr}"
                logging.error(error_msg)
                return {"success": False, "error": error_msg}

            return {"success": True, "message": "Batch processing completed successfully."}

        except Exception as e:
            error_msg = f"Error processing PDFs: {str(e)}"
            logging.error(error_msg)
            return {"success": False, "error": error_msg}



@app.route('/extract', methods=['POST'])
def extract_figures():
    """Extract figures from a PDF file, directory, or URL given its path."""
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided"), 400

    source = data.get("source")
    stat_file = data.get("stat_file")

    if not source:
        return jsonify(error="No source provided"), 400

    processor = PDFProcessor()
    
    # Check if source is a URL
    if source.startswith("http://") or source.startswith("https://"):
        pdf_path = processor.download_pdf(source)
        if not pdf_path:
            return jsonify(error="Failed to download PDF from URL"), 500
    else:
        pdf_path = os.path.abspath(source)  # Convert to absolute path

    # Check if it's a directory
    if os.path.isdir(pdf_path):
        result = processor.process_directory(pdf_path, stat_file)
    elif os.path.isfile(pdf_path) and pdf_path.lower().endswith('.pdf'):
        result = processor.process_single_pdf(pdf_path)
    else:
        return jsonify(error=f"Invalid file or path: {pdf_path}"), 400

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(error=result["error"]), 500


@app.route('/visualize', methods=['POST'])
def visualize_pdf():
    processor = PDFProcessor()
    data = request.get_json()
    if not data:
        return jsonify(error="No data provided"), 400

    source = data.get("source")
    intermediate = data.get("intermediate", False)

    if not source:
        return jsonify(error="No source provided"), 400

    abs_path = os.path.abspath(source)
    if os.path.isfile(abs_path) and abs_path.lower().endswith('.pdf'):
        result = processor.visualize_pdf(abs_path, intermediate)
    else:
        return jsonify(error=f"Invalid file or path: {abs_path}"), 400

    if result["success"]:
        return jsonify(result)
    else:
        return jsonify(error=result["error"]), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)