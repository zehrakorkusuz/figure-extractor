
# Figure Extractor API

Extract figures and tables from PDF documents using this Flask-based service. The Figure Extractor API provides a straightforward HTTP interface for PDFFigures 2.0, a robust academic figure extraction system developed by the Allen Institute for AI. 

This API wrapper makes it ideal for integration into various applications and workflows, particularly for Retrieval-Augmented Generation (RAG) applications.


### About PDFFigures 2.0
This API service is built on top of PDFFigures 2.0, a Scala-based project by the Allen Institute for AI. PDFFigures 2.0 is specifically designed to extract figures, captions, tables, and section titles from scholarly documents in computer science domain. The original work is described in their academic paper: "PDFFigures 2.0: Mining Figures from Research Papers" (Clark and Divvala, 2016). You can read the paper [here](https://ai2-website.s3.amazonaws.com/publications/pdf2.0.pdf) and visit the [PDFFigures 2.0 website](http://pdffigures2.allenai.org/).

```
┌─────────────────┐      ┌──────────────────┐      ┌────────────────┐
│   Your App      │ HTTP │  Figure Extractor │ JNI  │  PDFFigures    │
│  (Any Language) │──────►      API         │──────►     2.0        │
│                 │      │  (Flask Service)  │      │  (Scala/JVM)   │
└─────────────────┘      └──────────────────┘      └────────────────┘
```
## Features

- PDF figure and table extraction
- Support for local and remote PDF files
- Batch processing capabilities
- Statistical analysis of processed PDFs
- Docker support for easy deployment
- Visualization options for PDF parsing

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/figure-extractor.git
   cd figure-extractor
   ```

2. Build the Docker image:
   ```bash
   docker build -t figure-extractor .
   ```

## Quick Start

1. Start the service:
   ```bash
   docker run -v $(pwd)/data:/pdffigures2/data -p 5001:5001 figure-extractor
   ```

2. Extract figures from a PDF:
   ```bash
   curl -X POST http://localhost:5001/extract \
        -H "Content-Type: application/json" \
        -d '{"source": "data/input/ShowcaseUserGuide.pdf"}'
   ```

⚠️ **Local Directory Mounting** 

The service requires access to your local files through Docker volume mounting. When running the container, modify the `$(pwd)/data` path to point to your local directory containing the PDFs:

For example, if your PDFs are in `/home/user/documents/pdfs`, use:
```bash
docker run -v /home/user/documents/pdfs:/pdffigures2/data -p 5001:5001 figure-extractor
```

## API Endpoints

### Extract Figures
**Endpoint:** `POST /extract`

Process a single PDF file or directory of PDFs to extract figures.

#### Options:

1. Process a local PDF:
```bash
curl -X POST http://localhost:5001/extract \
     -H "Content-Type: application/json" \
     -d '{"source": "data/input/sample.pdf"}'
```

2. Process a remote PDF:
```bash
curl -X POST http://localhost:5001/extract \
     -H "Content-Type: application/json" \
     -d '{"source": "https://arxiv.org/pdf/2307.03550.pdf"}'
```

3. Process a directory with statistics:
```bash
curl -X POST http://localhost:5001/extract \
     -H "Content-Type: application/json" \
     -d '{
           "source": "data/input/",
           "stat_file": "data/stat.json"
         }'
```

## Directory Structure

```
figure-extractor/
├── data/
│   ├── input/    # PDFs here
│   └── output/
         └── figures/ # Extracted figures will appear here as .png files
         └── metadata/ # these files are particularly usefull to implement in retrieval layer
├── Dockerfile
└── README.md
```

In order to reproduce the same results you can delete the output file and run the previous 3 curl commands. 

## Configuration

### Docker Volume Mapping

The default configuration maps the local `data` directory to `/pdffigures2/data` in the container. To use a different directory:

```bash
docker run -v /path/to/your/data:/pdffigures2/data -p 5001:5001 figure-extractor
```

### Statistics Output

When processing multiple PDFs, you can generate a statistics file by including the `stat_file` parameter. The statistics file will contain:
- Processing status for each PDF
- Number of figures extracted
- Processing time
- Any errors encountered

## Troubleshooting

### Common Issues

1. **File Not Found Error**
   - Ensure the PDF file exists in the mapped data directory
   - Check file permissions
   - Verify the path is relative to the container's data directory

2. **Connection Refused**
   - Confirm the service is running
   - Check if port 5001 is available
   - Verify Docker container is running properly

3. **Processing Timeout**
   - Large PDFs may require increased timeout settings
   - Consider processing files individually rather than in batch

## Limitations

- Maximum file size depends on available system resources
- Processing time increases with PDF complexity
- Some highly complex or poorly formatted PDFs may not process correctly

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For support or queries, please open an issue in the GitHub repository.


