# tCam-Mini-Rev 4 Advanced Leaf Analysis Implementation Plan

## Project Overview

**Objective**: Replace the current ESP32-S3 + MLX90640 thermal camera with a tCam-Mini-Rev 4 + FLIR Lepton 3.5 system that can identify individual leaves and perform detailed temperature analysis per leaf and across the leaf population.

**Key Improvements**:
- **20x Resolution Increase**: From 32×24 to 160×120 pixels
- **Professional Sensor**: FLIR Lepton 3.5 vs consumer MLX90640
- **Advanced Analytics**: Per-leaf temperature analysis vs simple overall statistics
- **Computer Vision**: Automated leaf identification and segmentation

## Technical Architecture

### Processing Strategy
**Decision**: Process images on BeaglePlay rather than tCam-Mini
- **Rationale**: BeaglePlay has significantly more computational resources
- **Benefits**: Full Python/OpenCV ecosystem, easier development, more sophisticated algorithms
- **Trade-off**: Need to transfer thermal images over WiFi (~19KB per 160×120 frame)

### Data Flow Architecture
```
tCam-Mini (FLIR Lepton 3.5) 
    ↓ [WiFi - Thermal Images + Raw Temperature Data]
BeaglePlay (Computer Vision Processing)
    ↓ [Leaf Identification & Temperature Analysis]
Greenhouse Monitoring Dashboard
    ↓ [Enhanced VPD Calculations]
Environmental Control Systems
```

## Implementation Phases

### Phase 1: Basic tCam-Mini Setup (Week 1)
**Goal**: Get tCam-Mini operational and understand its capabilities

#### Step 1.1: Hardware Setup
- [ ] Connect tCam-Mini to USB hub and power up
- [ ] Install tCam desktop application on development machine
- [ ] Verify basic thermal imaging functionality
- [ ] Test radiometric mode (temperature data per pixel)

#### Step 1.2: API Discovery
- [ ] Document tCam-Mini HTTP API endpoints
- [ ] Understand JSON data formats for:
  - Raw thermal images
  - Temperature arrays (160×120)
  - Camera configuration options
- [ ] Test image capture rates and quality

#### Step 1.3: Initial Testing
- [ ] Capture thermal images of greenhouse plants
- [ ] Analyze temperature data quality and range
- [ ] Document optimal camera positioning and settings

**Deliverables**:
- tCam-Mini operational documentation
- API endpoint reference
- Sample thermal images of greenhouse plants

### Phase 2: BeaglePlay Communication (Week 1-2)
**Goal**: Establish reliable communication between tCam-Mini and BeaglePlay

#### Step 2.1: Network Setup
- [ ] Configure tCam-Mini WiFi to connect to greenhouse network
- [ ] Assign static IP address for reliable communication
- [ ] Test network connectivity and latency

#### Step 2.2: Basic HTTP Client
- [ ] Create Python script on BeaglePlay to fetch thermal images
- [ ] Implement error handling and retry logic
- [ ] Test image transfer reliability and performance

#### Step 2.3: Integration with Existing System
- [ ] Extend `precision_sensors_server.py` with tCam-Mini support
- [ ] Create new API endpoint: `/api/thermal_advanced`
- [ ] Maintain backward compatibility with existing thermal API

**Deliverables**:
- Reliable WiFi communication
- Basic thermal image fetching on BeaglePlay
- Updated server with tCam-Mini integration

### Phase 3: Computer Vision Development (Week 2-3)
**Goal**: Implement leaf identification and segmentation algorithms

#### Step 3.1: Environment Setup
- [ ] Install OpenCV and dependencies on BeaglePlay:
  ```bash
  pip install opencv-python numpy scipy scikit-image
  ```
- [ ] Set up image processing development environment
- [ ] Create test dataset of thermal greenhouse images

#### Step 3.2: Leaf Segmentation Algorithm
**Approach**: Traditional computer vision with temperature-based segmentation

```python
def identify_leaves(thermal_image, temperature_array):
    """
    Identify individual leaves in thermal image
    
    Args:
        thermal_image: 160x120 thermal image
        temperature_array: 160x120 temperature values
    
    Returns:
        list of leaf regions with boundaries and temperature data
    """
    # 1. Temperature thresholding (leaves typically warmer than background)
    leaf_mask = temperature_array > background_threshold
    
    # 2. Morphological operations to clean noise
    cleaned_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel)
    
    # 3. Connected component analysis
    num_labels, labels = cv2.connectedComponents(cleaned_mask)
    
    # 4. Filter by size and shape to validate leaves
    valid_leaves = []
    for label in range(1, num_labels):
        region = (labels == label)
        if validate_leaf_region(region):
            valid_leaves.append(region)
    
    return valid_leaves
```

#### Step 3.3: Algorithm Development Tasks
- [ ] Implement temperature-based thresholding
- [ ] Add morphological operations for noise reduction
- [ ] Develop connected component analysis
- [ ] Create shape and size validation filters
- [ ] Test with various greenhouse conditions (lighting, plant types)

#### Step 3.4: Validation and Tuning
- [ ] Manual validation of leaf detection accuracy
- [ ] Parameter tuning for different plant types
- [ ] Performance optimization for real-time processing

**Deliverables**:
- Functional leaf identification algorithm
- Validation results and accuracy metrics
- Optimized parameters for greenhouse conditions

### Phase 4: Temperature Analysis Implementation (Week 3-4)
**Goal**: Extract and analyze temperature data for each identified leaf

#### Step 4.1: Per-Leaf Statistics
```python
def analyze_leaf_temperature(leaf_region, temperature_array):
    """
    Calculate comprehensive temperature statistics for a single leaf
    
    Returns:
        dict with min, max, mean, median, mode, std_dev, pixel_count
    """
    leaf_temps = temperature_array[leaf_region]
    
    return {
        'pixel_count': len(leaf_temps),
        'min_temp': np.min(leaf_temps),
        'max_temp': np.max(leaf_temps),
        'mean_temp': np.mean(leaf_temps),
        'median_temp': np.median(leaf_temps),
        'mode_temp': calculate_mode(leaf_temps),
        'std_dev_temp': np.std(leaf_temps),
        'centroid': calculate_centroid(leaf_region),
        'area_pixels': np.sum(leaf_region)
    }
```

#### Step 4.2: Population-Level Analysis
```python
def analyze_leaf_population(all_leaf_data):
    """
    Calculate statistics across all identified leaves
    
    Returns:
        population-level temperature statistics
    """
    all_temps = []
    for leaf in all_leaf_data:
        all_temps.extend(leaf['temperatures'])
    
    return {
        'total_leaves': len(all_leaf_data),
        'total_measurements': len(all_temps),
        'overall_min_temp': np.min(all_temps),
        'overall_max_temp': np.max(all_temps),
        'overall_mean_temp': np.mean(all_temps),
        'overall_median_temp': np.median(all_temps),
        'overall_mode_temp': calculate_mode(all_temps),
        'overall_std_dev_temp': np.std(all_temps)
    }
```

#### Step 4.3: Data Structure Design
```json
{
  "timestamp": "2025-07-27T10:00:00Z",
  "image_info": {
    "resolution": "160x120",
    "total_pixels": 19200,
    "camera_temp": 25.2
  },
  "leaf_analysis": {
    "total_leaves_detected": 15,
    "processing_time_ms": 245,
    "individual_leaves": [
      {
        "leaf_id": 1,
        "pixel_count": 245,
        "min_temp": 22.1,
        "max_temp": 24.8,
        "mean_temp": 23.4,
        "median_temp": 23.3,
        "mode_temp": 23.2,
        "std_dev_temp": 0.8,
        "centroid": [80, 60],
        "area_pixels": 245,
        "bounding_box": [70, 50, 90, 70]
      }
    ],
    "population_statistics": {
      "total_measurements": 3680,
      "overall_min_temp": 21.8,
      "overall_max_temp": 25.2,
      "overall_mean_temp": 23.6,
      "overall_median_temp": 23.5,
      "overall_mode_temp": 23.4,
      "overall_std_dev_temp": 1.2
    }
  },
  "background_analysis": {
    "non_leaf_pixels": 15520,
    "background_mean_temp": 19.2,
    "background_std_dev": 2.1
  },
  "quality_metrics": {
    "detection_confidence": 0.87,
    "image_clarity": 0.92,
    "temperature_stability": 0.95
  }
}
```

**Deliverables**:
- Complete temperature analysis functions
- Comprehensive data structure
- Validation against manual measurements

### Phase 5: System Integration (Week 4-5)
**Goal**: Integrate advanced leaf analysis with existing greenhouse monitoring system

#### Step 5.1: API Integration
- [ ] Extend `/api/thermal_advanced` endpoint with leaf analysis data
- [ ] Maintain backward compatibility with existing `/api/thermal_data`
- [ ] Add new endpoints:
  - `/api/leaf_analysis` - Current leaf analysis results
  - `/api/leaf_history` - Historical leaf temperature trends
  - `/api/leaf_count` - Leaf count over time

#### Step 5.2: Enhanced VPD Calculations
```python
def calculate_enhanced_vpd_with_leaves(leaf_data, air_temp, air_humidity):
    """
    Calculate VPD using leaf-specific temperatures
    
    Options:
    1. Average leaf temperature + air humidity
    2. Hottest leaf temperature + air humidity (stress indicator)
    3. Coolest leaf temperature + air humidity (optimal growth)
    4. Per-leaf VPD calculations
    """
    vpd_calculations = {
        'air_vpd': calculate_vpd(air_temp, air_humidity),
        'average_leaf_vpd': calculate_vpd(leaf_data['overall_mean_temp'], air_humidity),
        'max_leaf_vpd': calculate_vpd(leaf_data['overall_max_temp'], air_humidity),
        'min_leaf_vpd': calculate_vpd(leaf_data['overall_min_temp'], air_humidity),
        'per_leaf_vpd': [
            calculate_vpd(leaf['mean_temp'], air_humidity) 
            for leaf in leaf_data['individual_leaves']
        ]
    }
    return vpd_calculations
```

#### Step 5.3: Dashboard Updates
- [ ] Update web dashboard to display leaf analysis results
- [ ] Add visualizations:
  - Leaf count over time
  - Temperature distribution per leaf
  - Population-level temperature trends
  - Enhanced VPD calculations
- [ ] Create leaf detection overlay on thermal images

**Deliverables**:
- Fully integrated system with leaf analysis
- Enhanced VPD calculations using leaf data
- Updated dashboard with advanced visualizations

### Phase 6: Optimization & Production (Week 5-6)
**Goal**: Optimize performance and deploy for production use

#### Step 6.1: Performance Optimization
- [ ] Optimize image processing pipeline for real-time operation
- [ ] Implement caching and efficient data structures
- [ ] Add configurable processing frequency (1-5 Hz)
- [ ] Memory usage optimization

#### Step 6.2: Error Handling & Validation
- [ ] Robust error handling for network failures
- [ ] Data validation and quality checks
- [ ] Fallback to simple thermal analysis if leaf detection fails
- [ ] Logging and monitoring for production environment

#### Step 6.3: Wireless Production Deployment
- [ ] Replace USB connection with dumb power supply for tCam-Mini
- [ ] Configure automatic startup and recovery
- [ ] Test long-term reliability and stability
- [ ] Create monitoring and alerting for system health

#### Step 6.4: Documentation & Training
- [ ] Create user documentation for new features
- [ ] Document API changes and new endpoints
- [ ] Create troubleshooting guide
- [ ] Train users on interpreting leaf analysis data

**Deliverables**:
- Production-ready system with leaf analysis
- Complete documentation
- Performance benchmarks and reliability metrics

## Technical Requirements

### Hardware
- tCam-Mini-Rev 4 with FLIR Lepton 3.5 (available)
- BeaglePlay with sufficient processing power (available)
- Reliable WiFi network in greenhouse
- Dumb power supply for tCam-Mini production deployment

### Software Dependencies
```bash
# On BeaglePlay
pip install opencv-python numpy scipy scikit-image
pip install matplotlib seaborn  # For visualization
pip install pillow  # Image handling
```

### Performance Targets
- **Processing Speed**: 1-5 Hz real-time leaf analysis
- **Accuracy**: >90% leaf detection accuracy
- **Reliability**: 99%+ uptime in production
- **Latency**: <2 seconds from image capture to analysis results

## Risk Mitigation

### Technical Risks
1. **Leaf Detection Accuracy**: Develop robust validation and fallback mechanisms
2. **Processing Performance**: Optimize algorithms and consider hardware acceleration
3. **Network Reliability**: Implement robust retry logic and offline capabilities
4. **Power Management**: Design for continuous operation with minimal power

### Operational Risks
1. **Integration Complexity**: Maintain backward compatibility during transition
2. **User Adoption**: Provide clear documentation and training
3. **Maintenance**: Design for easy troubleshooting and updates

## Success Metrics

### Technical Metrics
- Leaf detection accuracy >90%
- Processing latency <2 seconds
- System uptime >99%
- Temperature measurement accuracy ±0.5°C

### Operational Metrics
- Enhanced VPD calculation accuracy
- Improved plant monitoring capabilities
- Reduced manual monitoring requirements
- Better crop management decisions

## Getting Started - Immediate Next Steps

### Step 1: Basic tCam-Mini Testing (This Week)
1. **Connect Hardware**: Plug tCam-Mini into USB hub and power up
2. **Install Software**: Download and install tCam desktop application
3. **Test Basic Functionality**: 
   - Capture thermal images
   - Verify radiometric mode
   - Test different camera settings
4. **Document API**: Explore HTTP endpoints and data formats

### Step 2: Initial Development Environment
1. **Set up development workspace** in `/tcam-mini-integration/`
2. **Create initial Python scripts** for tCam-Mini communication
3. **Test image capture and basic processing**

This plan provides a comprehensive roadmap from basic tCam-Mini setup to advanced leaf analysis capabilities, with clear deliverables and success metrics for each phase.