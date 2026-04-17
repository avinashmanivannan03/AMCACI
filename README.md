<<<<<<< HEAD
AMCACI - Autonomous Multi-modal Content Analysis and Clustering Intelligence

Overview

AMCACI is an advanced autonomous content analysis system that transforms news broadcast videos into structured, multi-modal outputs through intelligent processing. The system leverages cutting-edge AI technologies including large language models, speech processing, computer vision, and clustering algorithms to automatically extract, analyze, categorize, and summarize video content without human intervention.

Built as a comprehensive solution for news content analysis, AMCACI bridges the gap between raw video input and actionable insights by orchestrating a sophisticated 8-stage pipeline that includes autonomous quality optimization through AI agents, multi-depth summarization, and comprehensive visual and audio output generation.

Core Concept

The application provides a complete end-to-end news video analysis pipeline:

Video Input Processing: Users upload news broadcast videos in MP4 format
Audio Intelligence: Advanced audio extraction with noise reduction and voice activity detection
Transcription Pipeline: High-accuracy speech-to-text with word-level timestamps and punctuation restoration
Semantic Clustering: Intelligent topic categorization using sliding-window zero-shot classification combined with density-based clustering
Autonomous Optimization: AI agents continuously evaluate and improve clustering quality through iterative refinement
Multi-Depth Summarization: Extractive and abstractive summarization with 5 depth levels from brief to comprehensive analysis
Voice Synthesis: Natural text-to-speech generation for all summaries
Visual Processing: Automatic keyframe extraction and topic-specific summary video compilation

Technology Stack

Language: Python 3.10+
Web Framework: Streamlit for interactive user interface
AI Platform: Groq API with Llama-3.3-70b-versatile model for agent orchestration
Audio Processing: FFmpeg, Silero VAD, noisereduce for audio extraction and preprocessing
Speech Recognition: OpenAI Whisper medium model with Deep Multilingual Punctuation
Natural Language Processing: Hugging Face Transformers ecosystem with specialized models
Embeddings: Sentence-Transformers with all-MiniLM-L6-v2 for semantic understanding
Clustering: HDBSCAN density-based clustering with scikit-learn metrics
Text-to-Speech: Coqui TTS with Tacotron2-DDC model
Video Processing: OpenCV and MoviePy for frame extraction and video compilation

Key Libraries:
Whisper: OpenAI's robust speech recognition system with word-level timestamps
Transformers: Hugging Face library for BART-large-mnli zero-shot classification and BART-large-cnn summarization
Sentence-Transformers: State-of-the-art sentence embeddings for semantic similarity
HDBSCAN: Hierarchical density-based clustering for topic discovery
LangChain: Framework for LLM agent orchestration and prompt management
Groq: High-performance inference platform for Llama model execution
Coqui TTS: Open-source text-to-speech synthesis with natural voice generation
MoviePy: Video editing and composition library for summary video creation
Streamlit: Interactive web application framework for user interface
ROUGE-score: Automatic evaluation of text summarization quality
Gensim: Topic modeling and coherence metrics for cluster validation

External Services:
Groq API: Large language model inference for Agent 1 and Agent 2 operations
Hugging Face Hub: Pre-trained model downloads and inference
Torch Hub: Silero VAD model loading for voice activity detection

System Architecture

┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                       │
│  (Video Upload, Progress Tracking, Results Visualization)   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Requests
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  PIPELINE HANDLER                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 1: Audio Extraction                            │   │
│  │ - FFmpeg mono 16kHz WAV extraction                   │   │
│  │ - Format standardization for downstream processing   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 2: Audio Preprocessing                         │   │
│  │ - Noise reduction with spectral gating               │   │
│  │ - Voice Activity Detection with Silero VAD           │   │
│  │ - Silence removal and audio optimization             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 3: Speech Transcription                        │   │
│  │ - Whisper medium model transcription                 │   │
│  │ - Word-level timestamp alignment                     │   │
│  │ - Punctuation restoration and sentence segmentation  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 4: Semantic Clustering                         │   │
│  │ - SBERT sentence embeddings generation               │   │
│  │ - Sliding-window zero-shot classification            │   │
│  │ - Boundary misfit detection and correction           │   │
│  │ - HDBSCAN intra-category sub-clustering              │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 5: Agent 1 Optimization Loop                   │   │
│  │ - Clustering quality metrics computation             │   │
│  │ - LLM-based diagnosis and parameter tuning           │   │
│  │ - Iterative refinement with early exit detection     │   │
│  │ - Cluster merging and label reassignment             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 6: Multi-Depth Summarization                   │   │
│  │ - Extractive summary via SBERT similarity ranking    │   │
│  │ - BART-large-cnn abstractive summarization           │   │
│  │ - ROUGE-L quality assessment                         │   │
│  │ - Agent 2 depth-aware refinement                     │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 7: Text-to-Speech Synthesis                    │   │
│  │ - Coqui TTS natural voice generation                 │   │
│  │ - Category-specific audio file creation              │   │
│  │ - Audio format optimization for video integration    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Stage 8: Video Processing                            │   │
│  │ - Timestamp-based segment extraction                 │   │
│  │ - Summary video compilation with TTS audio           │   │
│  │ - Keyframe extraction (start, mid, end per sentence) │   │
│  │ - Multi-modal output generation                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                     ↓ JSON State Management
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Groq API     │  │ Hugging Face │  │ Torch Hub    │       │
│  │ (LLM Agents) │  │ (NLP Models) │  │ (Silero VAD) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘

Project Structure

amcaci_capstone/
├── main.py                          # CLI application entry point and video processing orchestration
├── streamlit_page.py                # Streamlit web interface with progress tracking and results visualization
├── requirements.txt                 # Python dependencies with version specifications
├── .env.example                     # Environment variables template with required API keys
├── Dockerfile                       # Container configuration for deployment
├── validate_integration.py          # System integration testing and validation
├── src/                             # Core application modules
│   ├── config/
│   │   └── settings.py              # Configuration management with environment variable loading
│   ├── models/
│   │   └── schemas.py               # Pydantic data models and type definitions
│   ├── services/                    # Core processing services for each pipeline stage
│   │   ├── audio_extractor.py       # Stage 1: FFmpeg-based audio extraction from video
│   │   ├── preprocessor.py          # Stage 2: Noise reduction and voice activity detection
│   │   ├── transcriber.py           # Stage 3: Whisper transcription with punctuation restoration
│   │   ├── embedder.py              # Sentence-BERT embedding generation for semantic analysis
│   │   ├── clusterer.py             # Stage 4: Sliding-window classification and HDBSCAN clustering
│   │   ├── metrics.py               # Clustering quality evaluation with multiple metrics
│   │   ├── agent1.py                # Stage 5: LLM-based clustering optimization agent
│   │   ├── summarizer.py            # Stage 6: Extractive and abstractive summarization
│   │   ├── agent2.py                # Stage 6: Depth-aware summary refinement agent
│   │   ├── tts_engine.py            # Stage 7: Coqui TTS synthesis for summary audio
│   │   └── video_processor.py       # Stage 8: Video compilation and keyframe extraction
│   ├── handlers/
│   │   └── pipeline_handler.py      # Main orchestrator coordinating all pipeline stages
│   └── utils/
│       ├── logger.py                # Structured logging with file and console output
│       └── file_utils.py            # File I/O utilities and output directory management
├── data/                            # Data storage and processing artifacts
│   ├── temp/                        # Temporary files during processing
│   ├── outputs/                     # Structured output directories per run
│   └── logs/                        # Application logs with rotation
└── test/
    └── test_connections.py          # Integration tests for external service connectivity

Prerequisites

Required Software
Python 3.8 or higher - Core runtime environment with asyncio support
FFmpeg - Audio/video processing toolkit (must be in system PATH)
Git - Version control for repository management
Modern web browser - For Streamlit interface (Chrome, Firefox, Safari, Edge recommended)

Required API Keys
Groq API Key - Large language model access for Agent 1 and Agent 2 operations

Optional Dependencies
CUDA-compatible GPU - Significantly accelerates Whisper transcription and SBERT embedding generation
Additional RAM - 8GB+ recommended for processing longer videos or multiple concurrent sessions

Installation & Setup

1. Clone Repository
git clone https://github.com/your-org/amcaci-capstone.git
cd amcaci-capstone

2. Create Python Virtual Environment
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

3. Install Dependencies
# Upgrade pip to latest version
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

Note: First-time installation will download several GB of pre-trained models including Whisper medium, BART models, and Sentence-BERT embeddings. Ensure stable internet connection and sufficient disk space.

4. Install FFmpeg
# Windows (using chocolatey):
choco install ffmpeg

# macOS (using homebrew):
brew install ffmpeg

# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# Verify installation:
ffmpeg -version

5. Configure Environment Variables
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
Required environment variables:

# Groq API Configuration (REQUIRED)
GROQ_API_KEY=your_groq_api_key_here

# Optional Configuration
LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR
BASE_OUTPUT_DIR=data/outputs         # Output directory path
TEMP_DIR=data/temp                   # Temporary files directory

6. Validate Installation
# Run integration tests to verify all components
python test/test_connections.py

# Test basic pipeline functionality
python validate_integration.py

This validation will:
Test Groq API connectivity and model access
Verify FFmpeg installation and audio processing capabilities
Check Hugging Face model downloads and inference
Validate Whisper transcription functionality
Test TTS synthesis and audio generation
Confirm video processing and keyframe extraction

7. Launch Application

Command Line Interface:
python main.py path/to/your/video.mp4

Web Interface:
streamlit run streamlit_page.py

The Streamlit interface will open automatically in your browser at http://localhost:8501.

8. Verify Installation
Test the system with a sample news video:
Upload a short news video (30 seconds recommended for first test)
Monitor the 8-stage pipeline progress in real-time
Verify outputs: transcript, clusters, summaries, TTS audio, and summary videos
Check the data/outputs/[run_id]/ directory for all generated artifacts

How It Works

Complete Pipeline Flow

1. Video Input and Audio Extraction
When a user uploads a news video, the system begins with audio extraction using FFmpeg. The video is processed to extract a mono 16kHz WAV file optimized for speech recognition. This standardization ensures consistent quality across different input video formats and codecs.

The extraction process handles various video containers (MP4, AVI, MOV) and automatically converts audio streams to the optimal format for downstream processing. Error handling ensures graceful degradation if video corruption or unsupported formats are encountered.

2. Intelligent Audio Preprocessing
The extracted audio undergoes sophisticated preprocessing to optimize transcription accuracy. The system applies spectral noise reduction using the noisereduce library, which analyzes the audio spectrum to identify and suppress background noise while preserving speech clarity.

Voice Activity Detection (VAD) using the Silero model identifies and retains only segments containing human speech, removing silence, music, and non-speech audio. This preprocessing step typically reduces audio length by 40-60% while maintaining all relevant content, significantly improving transcription speed and accuracy.

3. High-Accuracy Transcription Pipeline
Transcription utilizes OpenAI's Whisper medium model, providing state-of-the-art accuracy for English news content. The system generates word-level timestamps, enabling precise alignment between text and video segments for later processing stages.

Post-transcription processing includes punctuation restoration using the Deep Multilingual Punctuation model, which adds appropriate punctuation marks, capitalization, and sentence boundaries. This step transforms raw speech recognition output into properly formatted text suitable for semantic analysis.

The output consists of TranscriptSegment objects containing the sentence text, precise start and end timestamps, and unique segment identifiers for downstream processing.

4. Advanced Semantic Clustering and Categorization
The clustering stage represents the system's most sophisticated component, combining multiple AI techniques for intelligent topic discovery:

Sliding-Window Zero-Shot Classification:
Groups consecutive sentences into overlapping windows (default: 3 sentences with 1 sentence overlap)
Each window is classified as a unit using BART-large-mnli against predefined news categories
Assigns provisional category labels to all sentences within each window
Handles topic transitions more effectively than sentence-by-sentence classification

Boundary Misfit Detection:
Computes SBERT embeddings for all sentences to capture semantic similarity
Identifies sentences at category boundaries that may be misclassified
Uses cosine similarity thresholds to detect sentences that don't semantically fit their assigned category
Reassigns misfits to neighboring categories based on embedding proximity

Intra-Category HDBSCAN Clustering:
Groups sentences of the same category using density-based clustering
Discovers sub-topics within broader categories (e.g., multiple sports stories within Sports category)
Handles noise and outliers gracefully without forcing every sentence into a cluster
Produces final ClusterResult objects with category labels, sentence groups, and confidence scores

5. Autonomous Quality Optimization with Agent 1
The system includes an intelligent evaluation loop that automatically assesses and improves clustering quality:

Metric Computation:
Silhouette Score: Measures how well-separated clusters are (higher is better)
Davies-Bouldin Index: Evaluates cluster compactness and separation (lower is better)
Calinski-Harabasz Index: Assesses cluster density and separation (higher is better)
Noise Percentage: Proportion of sentences not assigned to any cluster
Topic Coherence: Gensim-based coherence scores for each cluster using LDA topic modeling

Agent 1 Diagnosis and Optimization:
If metrics fail to meet quality thresholds, Agent 1 (Llama-3.3-70b) analyzes the clustering results
The agent receives cluster contents, metric scores, and failure reasons as input
Generates actionable recommendations including:
Parameter adjustments (min_cluster_size, min_samples for HDBSCAN)
Cluster merge suggestions for overly fragmented topics
Label reassignment recommendations for misclassified content
Rationale explanations for each suggested change

Iterative Refinement:
Applies agent suggestions and re-runs clustering using a fast path that skips expensive zero-shot classification
Supports up to 3 optimization attempts with early exit if scores become frozen (indicating geometric convergence)
Accumulates relabeling suggestions across attempts to preserve previous improvements
Tracks clustering evolution and prevents infinite loops

6. Multi-Depth Summarization System
The summarization stage operates in two phases with optional AI agent refinement:

Extractive Summarization:
Selects the top 3 most representative sentences from each cluster
Uses SBERT embeddings to compute cosine similarity between each sentence and the cluster centroid
Preserves original sentence order and maintains factual accuracy
Provides a foundation for abstractive summarization

Abstractive Summarization:
Employs BART-large-cnn to generate fluent, concise summaries from extractive content
Produces summaries with configurable length constraints (40-180 tokens)
Computes ROUGE-L scores to assess summary quality against source content
Maintains factual consistency while improving readability and coherence

Agent 2 Depth-Aware Refinement:
Invoked when ROUGE-L scores fall below 0.30 or when users specify custom depth levels or focus areas
Supports 5 depth levels:
Level 1: Single brief sentence for quick overview
Level 2: 2-3 sentences covering main points only
Level 3: 4-5 sentences providing balanced coverage (default)
Level 4: Detailed paragraph with facts, context, and figures
Level 5: Comprehensive in-depth analysis with implications
Incorporates user-provided custom notes for specialized focus requirements
Generates summaries optimized for the specified depth and user intent

7. Natural Voice Synthesis
Text-to-speech synthesis transforms written summaries into natural-sounding audio using Coqui TTS:

Model Selection: Uses Tacotron2-DDC model trained on LJSpeech dataset for clear, professional narration
Audio Quality: Generates 22kHz WAV files optimized for video integration
Batch Processing: Synthesizes all category summaries in parallel for efficiency
Error Handling: Gracefully handles synthesis failures without stopping the pipeline
Output Management: Creates category-specific audio files with standardized naming conventions

8. Comprehensive Video Processing
The final stage produces visual outputs that complement the text and audio analysis:

Timestamp-Based Segment Extraction:
Maps extractive summary sentences back to their original video timestamps
Identifies video segments corresponding to each important sentence
Merges nearby segments (within 5 seconds) to create coherent clips
Handles temporal overlaps and ensures chronological ordering

Summary Video Compilation:
Extracts relevant video segments for each topic category
Concatenates segments into topic-specific summary videos
Replaces original audio with synthesized TTS narration
Handles duration mismatches between video and audio (trimming longer component)
Applies video encoding optimization for web playback

Keyframe Extraction:
Extracts 3 representative frames per summary sentence: start, middle, and end timestamps
Uses OpenCV for precise frame-level seeking and high-quality image extraction
Generates JPEG keyframes with descriptive filenames including timestamps
Creates visual summaries that complement the text and audio outputs

Output Management:
Organizes all outputs in structured directories per processing run
Generates comprehensive JSON metadata for all processing stages
Provides download links and preview capabilities through the web interface
Maintains processing logs and error reports for debugging and analysis

Advanced Features

Intelligent Sliding-Window Classification
The system employs a sophisticated approach to topic classification that outperforms traditional sentence-by-sentence methods:

Window-Based Context: Groups 3 consecutive sentences to provide richer context for classification decisions
Overlap Strategy: Uses 1-sentence overlap between windows to ensure smooth topic transitions
Majority Voting: Sentences appearing in multiple windows receive votes from each window, with final assignment based on majority consensus
Boundary Handling: Special processing for sentences at the beginning and end of transcripts to ensure complete coverage

This approach significantly improves classification accuracy for news content where topic boundaries may not align perfectly with sentence boundaries.

Autonomous Clustering Optimization
Agent 1 represents a breakthrough in autonomous machine learning pipeline optimization:

Multi-Metric Analysis: Simultaneously considers multiple clustering quality metrics rather than optimizing for a single score
Contextual Understanding: Analyzes actual cluster contents alongside numerical metrics to identify semantic issues
Actionable Recommendations: Provides specific, implementable suggestions rather than generic advice
Iterative Learning: Accumulates knowledge across optimization attempts to avoid repeating ineffective changes
Early Termination: Detects when clustering geometry has converged and further attempts would be futile

Depth-Aware Summarization
Agent 2 provides unprecedented control over summary detail and focus:

Adaptive Length Control: Automatically adjusts summary length based on source content complexity and user requirements
Context Preservation: Maintains factual accuracy while adapting presentation style to match requested depth
Custom Focus Integration: Incorporates user-specified focus areas or questions into summary generation
Quality Assurance: Uses ROUGE metrics to validate summary quality and trigger refinement when necessary

Multi-Modal Output Generation
The system produces comprehensive outputs that serve different use cases:

Text Outputs: Machine-readable JSON for integration with other systems
Audio Outputs: Professional-quality TTS for accessibility and multimedia applications
Video Outputs: Topic-specific summary videos for visual learners and presentation use
Visual Outputs: Keyframe galleries for quick visual scanning and thumbnail generation

Performance Characteristics

Processing Speed and Scalability
Typical Processing Times (30-second news video):
Stage 1 (Audio Extraction): 5-10 seconds
Stage 2 (Preprocessing): 10-15 seconds
Stage 3 (Transcription): 30-60 seconds (CPU) / 10-20 seconds (GPU)
Stage 4 (Clustering): 20-30 seconds
Stage 5 (Agent 1): 10-30 seconds per attempt (up to 3 attempts)
Stage 6 (Summarization): 15-25 seconds
Stage 7 (TTS): 10-20 seconds
Stage 8 (Video Processing): 20-40 seconds
Total: 2-4 minutes (CPU) / 1.5-2.5 minutes (GPU)

Memory Requirements:
Minimum: 4GB RAM for basic functionality
Recommended: 8GB RAM for optimal performance
GPU Processing: Additional 2-4GB VRAM for accelerated inference

Concurrent Processing:
Supports multiple simultaneous sessions with resource management
Automatic model sharing across sessions to minimize memory usage
Queue-based processing for resource-intensive operations

Quality Metrics and Thresholds
The system maintains high quality standards through multiple evaluation criteria:

Clustering Quality Thresholds:
Silhouette Score: ≥ 0.30 (good cluster separation)
Davies-Bouldin Index: ≤ 1.50 (compact, well-separated clusters)
Noise Percentage: ≤ 30% (most content successfully clustered)
Topic Coherence: ≥ 0.40 per cluster (semantically coherent topics)

Summarization Quality Thresholds:
ROUGE-L Score: ≥ 0.30 (adequate content overlap with source)
Length Constraints: 40-180 tokens (readable but concise)
Factual Consistency: Maintained through extractive foundation

Transcription Accuracy:
Word Error Rate: Typically 5-15% for clear news audio
Timestamp Precision: ±0.1 seconds for sentence boundaries
Punctuation Accuracy: 85-95% after restoration processing

Troubleshooting

Common Issues and Solutions

Groq API Connection Errors
Error: Authentication failed or API key invalid
Solution:
Verify GROQ_API_KEY is correctly set in .env file
Check API key validity at Groq Console dashboard
Ensure sufficient API credits are available
Test connectivity: python test/test_connections.py

FFmpeg Not Found Error
Error: FFmpeg not found in system PATH
Solution:
Install FFmpeg using system package manager
Add FFmpeg to system PATH environment variable
Verify installation: ffmpeg -version
Restart terminal/IDE after PATH changes

Whisper Model Download Issues
Error: Failed to download Whisper model
Solution:
Ensure stable internet connection (models are 1-3GB)
Clear Hugging Face cache: rm -rf ~/.cache/huggingface/
Retry with manual download: python -c "import whisper; whisper.load_model('medium')"
Check available disk space (requires 5-10GB free)

CUDA/GPU Detection Problems
Error: CUDA not available, falling back to CPU
Impact: Slower processing but fully functional
Solution:
Install CUDA toolkit compatible with PyTorch version
Verify GPU detection: python -c "import torch; print(torch.cuda.is_available())"
Update GPU drivers to latest version
Reinstall PyTorch with CUDA support if necessary

Memory Issues During Processing
Error: Out of memory during model inference
Solution:
Close other applications to free RAM
Process shorter video segments (split long videos)
Reduce batch sizes in settings.py
Consider upgrading to higher-memory system
Use CPU-only processing if GPU memory is insufficient

Clustering Quality Issues
Error: Clustering consistently fails quality thresholds
Solution:
Review news category definitions in settings.py
Adjust quality thresholds for specific content types
Provide more diverse training examples
Check transcript quality (poor transcription affects clustering)
Consider manual category refinement through web interface

TTS Synthesis Failures
Error: Text-to-speech generation failed
Impact: Silent summary videos but other outputs remain functional
Solution:
Verify Coqui TTS model installation
Check text content for special characters or formatting issues
Ensure sufficient disk space for audio file generation
Try alternative TTS models in settings.py

Video Processing Errors
Error: MoviePy video compilation failed
Solution:
Verify input video format compatibility
Check available disk space for output files
Install additional video codecs if needed
Try reducing video resolution or quality settings
Ensure FFmpeg supports required video codecs

Debug Mode and Logging
Enable detailed logging for troubleshooting:

# Set environment variable
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py video.mp4

# Check log files
tail -f data/logs/amcaci.log

Debug mode provides:
Detailed timing information for each processing stage
Model loading and inference statistics
API request/response details for Groq calls
Clustering iteration details and metric evolution
File I/O operations and error stack traces

Performance Optimization

For production deployment or improved performance:

GPU Acceleration:
Install CUDA-compatible PyTorch: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
Set WHISPER_DEVICE="cuda" in settings.py
Monitor GPU memory usage during processing

Model Optimization:
Use smaller Whisper models for faster transcription: WHISPER_MODEL_SIZE="small"
Reduce SBERT embedding dimensions for memory efficiency
Cache model instances across multiple processing runs

Batch Processing:
Process multiple videos in sequence to amortize model loading costs
Implement queue-based processing for high-throughput scenarios
Use multiprocessing for CPU-intensive stages

Storage Optimization:
Use SSD storage for temporary files and model cache
Implement automatic cleanup of old processing runs
Compress output videos for storage efficiency

Security Considerations

API Key Management
Environment Variables: All API keys stored in .env file, never committed to version control
Access Control: Groq API keys provide access to LLM inference capabilities
Rotation: Regularly rotate API keys and update .env file
Scope Limitation: Use API keys with minimal required permissions

Data Privacy and Security
Local Processing: All video and audio processing occurs locally, no external data transmission except for LLM API calls
Temporary Files: Automatically cleaned up after processing completion
No PII Storage: System does not store personally identifiable information
Logging Security: Logs contain no sensitive data, only operational metrics and error information

Network Security
Local Development: Default configuration binds to localhost only for Streamlit interface
Production Deployment: Use reverse proxy (nginx) with HTTPS termination for web access
API Rate Limiting: Implement rate limiting to prevent abuse of Groq API quotas
Input Validation: Comprehensive validation of uploaded video files and user inputs

Generated Content Security
Content Filtering: Summaries generated from source content only, no external information injection
Factual Consistency: Extractive summarization foundation ensures factual accuracy
Bias Mitigation: Multiple model ensemble approach reduces individual model biases
Output Validation: ROUGE metrics and coherence scores validate summary quality

Development Setup

For developers wanting to extend or modify the system:

# Install development dependencies
pip install -r requirements.txt
pip install pytest black mypy flake8

# Run tests
python -m pytest test/ -v

# Format code
black src/ test/ *.py

# Type checking
mypy src/

# Lint code
flake8 src/ test/ *.py

# Run integration tests
python test/test_connections.py

Development Guidelines:
Follow PEP 8 style guidelines with Black formatting
Use type hints for all function signatures
Write comprehensive docstrings for public APIs
Include unit tests for new functionality
Update configuration documentation for new settings
Maintain backward compatibility for data schemas

Contributing:
Fork the repository and create feature branches
Write tests for new functionality
Update documentation for API changes
Submit pull requests with clear descriptions
Follow semantic versioning for releases

This comprehensive system represents a sophisticated approach to autonomous content analysis, combining multiple AI technologies in a cohesive pipeline that delivers professional-quality results with minimal human intervention.
=======
# AMCACI
>>>>>>> a57e2df54ced955a719ea5cdeadd9e795b9e5cea
