# Jetson Orin Nano Super + SAM2 Leaf Segmentation Project Plan

## 🎯 Project Overview

**Goal**: Develop AI-powered leaf segmentation system using Meta's SAM2 framework to extract precise leaf temperatures from thermal imagery for enhanced VPD calculations.

**Hardware Upgrade**: BeaglePlay → Jetson Orin Nano Super (100 TOPS AI performance)

**Timeline**: 2-week development window before Jetson arrival, then porting and optimization

---

## 📋 Project Phases

### Phase 1: Development Environment Setup (Week 1)
**Platform**: Laptop development
**Data Source**: Static thermal images/videos from `/home/lio/Desktop/`

#### 1.1 SAM2 Installation & Setup
- [ ] Clone SAM2 repository: `https://github.com/facebookresearch/sam2`
- [ ] Install dependencies (PyTorch, CUDA if available)
- [ ] Download pre-trained SAM2 models
- [ ] Verify SAM2 functionality with test images
- [ ] Create virtual environment for project isolation

#### 1.2 Thermal Data Analysis
- [ ] Analyze existing thermal images (`thermal_image_*.png`)
- [ ] Analyze thermal videos (`thermal_video_*.mp4`)
- [ ] Understand thermal data format and temperature encoding
- [ ] Create thermal image visualization tools
- [ ] Document thermal data characteristics

#### 1.3 Initial Segmentation Tests
- [ ] Test SAM2 on thermal images (direct application)
- [ ] Evaluate segmentation quality for plant/leaf detection
- [ ] Identify challenges with thermal vs RGB imagery
- [ ] Document initial findings and limitations

### Phase 2: SAM2 Adaptation for Thermal Imagery (Week 2)
**Focus**: Optimize SAM2 for thermal plant segmentation

#### 2.1 Thermal Image Preprocessing
- [ ] Convert thermal data to SAM2-compatible formats
- [ ] Implement thermal colormap conversions
- [ ] Create contrast enhancement algorithms
- [ ] Develop thermal normalization techniques
- [ ] Test different thermal visualization approaches

#### 2.2 Leaf Detection Strategy
- [ ] Develop leaf identification prompts for SAM2
- [ ] Implement automatic prompt generation
- [ ] Create leaf vs background discrimination
- [ ] Handle overlapping/clustered leaves
- [ ] Optimize for plant canopy scenarios

#### 2.3 Segmentation Pipeline Development
- [ ] Create end-to-end segmentation pipeline
- [ ] Implement batch processing for multiple images
- [ ] Add segmentation quality metrics
- [ ] Create visualization tools for results
- [ ] Develop debugging and analysis tools

### Phase 3: Temperature Extraction & Analysis (Week 3)
**Focus**: Convert segmented regions to temperature statistics

#### 3.1 Temperature Conversion
- [ ] Implement thermal pixel → temperature conversion
- [ ] Handle tCam-Mini specific thermal encoding
- [ ] Validate temperature accuracy against known values
- [ ] Create temperature calibration system
- [ ] Document conversion methodology

#### 3.2 Per-Leaf Statistics
- [ ] Extract temperature data from segmented regions
- [ ] Calculate per-leaf statistics:
  - [ ] Minimum temperature
  - [ ] Maximum temperature
  - [ ] Mean temperature
  - [ ] Median temperature
  - [ ] Mode temperature
  - [ ] Standard deviation
- [ ] Handle edge cases (small segments, noise)
- [ ] Create statistical validation tools

#### 3.3 Data Validation & Quality Control
- [ ] Implement outlier detection
- [ ] Create temperature range validation
- [ ] Add segment size filtering
- [ ] Develop quality metrics for segments
- [ ] Create data export formats (JSON, CSV)

### Phase 4: Jetson Orin Nano Preparation (Week 4)
**Focus**: Prepare for hardware transition

#### 4.1 Jetson Compatibility Assessment
- [ ] Research SAM2 performance on Jetson Orin Nano
- [ ] Identify potential optimization requirements
- [ ] Plan memory and compute resource usage
- [ ] Create performance benchmarking tools
- [ ] Document hardware requirements

#### 4.2 Code Optimization
- [ ] Profile current implementation performance
- [ ] Identify bottlenecks and optimization opportunities
- [ ] Implement GPU acceleration where possible
- [ ] Create configurable processing parameters
- [ ] Optimize for real-time processing

#### 4.3 Deployment Preparation
- [ ] Create installation scripts for Jetson
- [ ] Package dependencies and models
- [ ] Create configuration management system
- [ ] Develop testing and validation suite
- [ ] Document deployment procedures

### Phase 5: Jetson Integration & WiFi Streaming (Weeks 5-6)
**Focus**: Deploy to Jetson and integrate with tCam-Mini WiFi

#### 5.1 Jetson Setup & Deployment
- [ ] Set up Jetson Orin Nano Super
- [ ] Install JetPack and required software
- [ ] Deploy SAM2 and dependencies
- [ ] Validate performance on Jetson hardware
- [ ] Optimize for Jetson-specific features

#### 5.2 WiFi Integration
- [ ] Implement tCam-Mini WiFi streaming client
- [ ] Create real-time image processing pipeline
- [ ] Add streaming buffer management
- [ ] Implement frame rate optimization
- [ ] Create network error handling

#### 5.3 System Integration
- [ ] Integrate with existing precision sensor system
- [ ] Create unified data API
- [ ] Implement enhanced VPD calculations
- [ ] Add web interface for results
- [ ] Create monitoring and logging systems

---

## 🛠️ Technical Architecture

### Core Components

#### 1. Thermal Image Processor
```python
class ThermalImageProcessor:
    - load_thermal_image()
    - convert_to_temperature()
    - normalize_for_sam2()
    - apply_preprocessing()
```

#### 2. SAM2 Leaf Segmenter
```python
class SAM2LeafSegmenter:
    - initialize_sam2_model()
    - generate_leaf_prompts()
    - segment_leaves()
    - post_process_segments()
```

#### 3. Temperature Analyzer
```python
class LeafTemperatureAnalyzer:
    - extract_segment_temperatures()
    - calculate_statistics()
    - validate_measurements()
    - export_results()
```

#### 4. Pipeline Controller
```python
class SegmentationPipeline:
    - process_single_image()
    - process_video_stream()
    - batch_process()
    - real_time_process()
```

### Data Flow
```
Thermal Image/Video → Preprocessing → SAM2 Segmentation → 
Temperature Extraction → Statistical Analysis → VPD Integration
```

---

## 📊 Success Metrics

### Phase 1-2: Segmentation Quality
- [ ] Successful leaf detection rate > 90%
- [ ] False positive rate < 10%
- [ ] Processing time < 5 seconds per image (laptop)
- [ ] Visual validation of segmentation accuracy

### Phase 3: Temperature Accuracy
- [ ] Temperature measurement accuracy ±0.5°C
- [ ] Statistical consistency across multiple measurements
- [ ] Successful outlier detection and filtering
- [ ] Validation against manual temperature measurements

### Phase 4-5: Performance
- [ ] Real-time processing capability on Jetson (>1 FPS)
- [ ] Memory usage < 4GB
- [ ] Stable WiFi streaming integration
- [ ] Integration with existing greenhouse monitoring system

---

## 🔧 Development Tools & Environment

### Required Software
- **Python 3.8+** with virtual environment
- **PyTorch** (latest stable with CUDA support)
- **OpenCV** for image processing
- **NumPy/SciPy** for numerical analysis
- **Matplotlib** for visualization
- **SAM2** framework from Meta

### Hardware Requirements
- **Development**: Laptop with GPU (if available)
- **Production**: Jetson Orin Nano Super
- **Camera**: tCam-Mini with WiFi capability
- **Storage**: Sufficient space for models and data

### Project Structure
```
greenhouse-monitoring/
├── jetson-sam2-segmentation/
│   ├── src/
│   │   ├── thermal_processor.py
│   │   ├── sam2_segmenter.py
│   │   ├── temperature_analyzer.py
│   │   └── pipeline_controller.py
│   ├── models/
│   │   └── sam2_pretrained/
│   ├── data/
│   │   ├── thermal_images/
│   │   ├── thermal_videos/
│   │   └── test_results/
│   ├── tests/
│   ├── docs/
│   └── scripts/
├── requirements.txt
└── README.md
```

---

## 📝 Documentation Requirements

### Technical Documentation
- [ ] SAM2 adaptation methodology
- [ ] Thermal image processing algorithms
- [ ] Temperature conversion formulas
- [ ] Statistical analysis methods
- [ ] Performance optimization techniques

### User Documentation
- [ ] Installation and setup guide
- [ ] Configuration parameters
- [ ] Usage examples and tutorials
- [ ] Troubleshooting guide
- [ ] API documentation

### Research Documentation
- [ ] Segmentation accuracy analysis
- [ ] Performance benchmarks
- [ ] Comparison with alternative approaches
- [ ] Lessons learned and recommendations

---

## 🚀 Next Immediate Actions

### This Week (Week 1)
1. **Set up development environment**
2. **Install and test SAM2**
3. **Analyze existing thermal data**
4. **Create initial segmentation tests**

### Priority Tasks
1. Clone SAM2 repository and set up environment
2. Load and analyze thermal images from Desktop
3. Test SAM2 on thermal imagery
4. Document initial findings and challenges

---

## 📞 Integration Points

### Existing Systems
- **Precision Sensors**: Air temperature and humidity data
- **tCam-Mini**: Thermal image source
- **Web Dashboard**: Results visualization
- **Data Logging**: Historical analysis

### Future Enhancements
- **Real-time VPD calculations** using leaf temperatures
- **Plant health monitoring** based on temperature patterns
- **Automated irrigation control** based on leaf stress indicators
- **Historical trend analysis** for optimization

---

*This plan will be updated and refined as development progresses and new requirements emerge.*