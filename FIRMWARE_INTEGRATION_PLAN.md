# BeagleConnect Freedom Firmware Integration Plan

## Current Issue
The BeagleConnect Freedom firmware development is scattered across multiple directories:
- Main project: `/home/lio/github/greenhouse-monitoring` (version controlled)
- Firmware: `/home/lio/greybus-host/cc1352-firmware.git` (separate git repo with custom changes)
- Build tools: `/home/lio/greybus-host/build-and-flash.sh` (not version controlled)

## Recommended Solution: Git Submodule Integration

### Step 1: Create Firmware Directory Structure
```bash
mkdir -p firmware/beagleconnect-freedom
mkdir -p firmware/tools
mkdir -p docs/firmware
```

### Step 2: Add Firmware as Git Submodule
```bash
# First, commit our custom firmware changes
cd /home/lio/greybus-host/cc1352-firmware.git
git add .
git commit -m "Add custom I2C protocol and Greybus enhancements for greenhouse monitoring"

# Add as submodule to main project
cd /home/lio/github/greenhouse-monitoring
git submodule add https://openbeagle.org/gsoc/greybus/cc1352-firmware.git firmware/beagleconnect-freedom
```

### Step 3: Move Build Tools to Main Repository
```bash
# Copy build script to main repo
cp /home/lio/greybus-host/build-and-flash.sh firmware/tools/
# Update paths in script to work with new location
```

### Step 4: Create Firmware Development Documentation
- Document Zephyr SDK setup process
- Document build and flash procedures
- Document custom modifications made to firmware
- Integration with greenhouse monitoring system

### Step 5: Update Main README
- Add firmware development section
- Document the complete development workflow
- Include submodule update instructions

## Benefits of This Approach

✅ **Version Control Integration**: All code in one repository
✅ **Preserves History**: Firmware repo maintains its git history
✅ **Version Pinning**: Can pin to specific firmware commits
✅ **Build Integration**: Build tools version controlled with project
✅ **Documentation**: Complete development workflow documented
✅ **Team Collaboration**: Other developers can easily set up entire system

## New Directory Structure
```
greenhouse-monitoring/
├── beagleplay_code/              # BeaglePlay Python server
├── infrastructure/               # Docker, configs, etc.
├── node-red-flows/              # Node-RED flows
├── firmware/                    # NEW: Firmware development
│   ├── beagleconnect-freedom/   # Git submodule
│   └── tools/
│       ├── build-and-flash.sh  # Build automation
│       └── setup-zephyr.sh     # Environment setup
├── docs/
│   └── firmware-development.md # Firmware dev guide
└── README.md                   # Updated with firmware info
```

## Migration Steps

1. **Backup Current Work**
   ```bash
   cp -r /home/lio/greybus-host /home/lio/greybus-host.backup
   ```

2. **Commit Firmware Changes**
   ```bash
   cd /home/lio/greybus-host/cc1352-firmware.git
   git add .
   git commit -m "Custom greenhouse monitoring firmware enhancements"
   ```

3. **Integrate with Main Project**
   ```bash
   cd /home/lio/github/greenhouse-monitoring
   mkdir -p firmware/tools docs/firmware
   git submodule add https://openbeagle.org/gsoc/greybus/cc1352-firmware.git firmware/beagleconnect-freedom
   cp /home/lio/greybus-host/build-and-flash.sh firmware/tools/
   ```

4. **Update Build Script Paths**
   - Modify `build-and-flash.sh` to work from new location
   - Update all hardcoded paths

5. **Create Documentation**
   - Document the custom firmware modifications
   - Create setup guide for new developers
   - Document integration with greenhouse system

6. **Test Integration**
   - Verify build process works from new location
   - Test firmware flash process
   - Confirm greenhouse system integration

## Alternative Options Considered

### Option A: Copy Everything to Main Repo
- ❌ Loses firmware git history
- ❌ Mixes different types of code
- ❌ Harder to track upstream firmware updates

### Option B: Keep Separate Repositories
- ❌ Fragmented development experience
- ❌ No version correlation between firmware and application
- ❌ Difficult for new developers to set up

### Option C: Monorepo Approach
- ❌ Major restructuring required
- ❌ Loses individual project identity
- ❌ Overly complex for this use case

## Conclusion

The Git submodule approach provides the best balance of:
- Code organization
- Version control integration
- Development workflow simplicity
- Preservation of existing work
- Future maintainability

This solution addresses your concern about scattered, unversioned code while maintaining the benefits of separate firmware development.
