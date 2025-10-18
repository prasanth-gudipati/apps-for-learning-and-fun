# VMS Debug Tool - GUI Canvas Size Settings

## 📐 **Overview**
The VMS Debug Tool web interface uses responsive design with specific canvas size settings optimized for desktop and laptop screens.

## 🖥️ **Main Canvas Dimensions**

### **Viewport Meta Tag**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```
- **Purpose**: Responsive design for different screen sizes
- **Behavior**: Adapts to device width, no initial zoom

### **Overall Container**
```css
.container {
    max-width: 1400px;           /* Maximum canvas width */
    margin: 0 auto;              /* Center alignment */
    display: grid;               /* CSS Grid layout */
    grid-template-columns: 350px 1fr;  /* Left panel + flexible right panel */
    gap: 20px;                   /* Space between panels */
    height: calc(100vh - 80px);  /* Full viewport height minus 80px margin */
}
```

### **Body Settings**
```css
body {
    font-family: 'Consolas', 'Monaco', monospace;
    margin: 0;
    padding: 10px 20px;          /* 10px top/bottom, 20px left/right */
    background-color: #f5f5f5;
}
```

## 📏 **Detailed Dimensions**

### **Main Layout Structure**
| Component | Width | Height | Notes |
|-----------|-------|--------|-------|
| **Maximum Canvas** | `1400px` | `calc(100vh - 80px)` | Responsive up to 1400px width |
| **Left Panel** | `350px` | `calc(100vh - 120px)` | Fixed width control panel |
| **Right Panel** | `1fr` (flexible) | `calc(100vh - 80px)` | Remaining space |
| **Panel Gap** | `20px` | - | Space between left and right panels |
| **Body Padding** | `20px` (sides) | `10px` (top/bottom) | Outer margins |

### **Left Panel (Control Panel)**
```css
.left-panel {
    background: white;
    border-radius: 8px;
    padding: 20px;                    /* Internal padding */
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    overflow-y: auto;                 /* Vertical scroll when needed */
    max-height: calc(100vh - 120px);  /* Viewport height minus 120px */
}
```

### **Right Panel - Output Area**
```css
#output {
    flex: 1;                          /* Takes remaining space */
    background-color: #1e1e1e;        /* Dark terminal theme */
    color: #d4d4d4;
    padding: 15px;                    /* Internal padding */
    overflow-y: auto;                 /* Vertical scroll */
    overflow-x: hidden;               /* No horizontal scroll */
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
    line-height: 1.4;
    border-radius: 4px;
    white-space: pre-wrap;
    word-wrap: break-word;
    border: 1px solid #333;
    max-height: calc(100vh - 160px);  /* Viewport height minus 160px */
    min-height: 400px;                /* Minimum height guarantee */
}
```

### **Tenant Details Panel**
```css
#tenant-details {
    flex: 1;                          /* Takes remaining space */
    background-color: #f8f9fa;        /* Light background */
    padding: 15px;
    overflow-y: auto;                 /* Vertical scroll */
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
    line-height: 1.4;
    border-radius: 4px;
    border: 1px solid #dee2e6;
    max-height: calc(100vh - 160px);  /* Viewport height minus 160px */
    min-height: 400px;                /* Minimum height guarantee */
}
```

## 🎯 **Key Design Principles**

### **Responsive Breakpoints**
- **Desktop Optimized**: Designed for screens 1400px+ wide
- **Adaptive Width**: Container scales down on smaller screens
- **Fixed Left Panel**: 350px width maintains usability
- **Flexible Right Panel**: Adapts to remaining space

### **Viewport Height Calculations**
| Element | Height Calculation | Purpose |
|---------|-------------------|---------|
| **Container** | `calc(100vh - 80px)` | Account for body padding and margins |
| **Left Panel** | `calc(100vh - 120px)` | Extra space for panel borders/shadows |
| **Output Areas** | `calc(100vh - 160px)` | Account for headers and panel chrome |
| **Minimum Height** | `400px` | Ensure usability on shorter screens |

### **Scrollbar Specifications**
```css
/* Custom scrollbar for output area */
#output::-webkit-scrollbar {
    width: 12px;                      /* Scrollbar width */
}

/* Custom scrollbar for left panel */
.left-panel::-webkit-scrollbar {
    width: 8px;                       /* Thinner scrollbar */
}
```

## 📱 **Error Popup Dimensions**
```css
.error-popup {
    background-color: white;
    border-radius: 12px;
    max-width: 600px;                 /* Maximum popup width */
    width: 90%;                       /* 90% of viewport width */
    max-height: 80vh;                 /* 80% of viewport height */
    overflow-y: auto;                 /* Scroll if content too long */
}
```

## 🎨 **Font and Spacing Settings**
- **Primary Font**: `'Consolas', 'Monaco', monospace`
- **Font Size**: `12px` (consistent across output areas)
- **Line Height**: `1.4` (readable spacing)
- **Border Radius**: `4px` to `12px` (rounded corners)
- **Shadows**: `0 2px 10px rgba(0,0,0,0.1)` (subtle elevation)

## 💡 **Optimization Notes**
1. **Performance**: CSS Grid provides efficient layout rendering
2. **Accessibility**: Minimum sizes ensure usability across devices
3. **Scrolling**: Strategic overflow settings prevent layout breaking
4. **Visual Hierarchy**: Size and spacing create clear content organization
5. **Responsive**: Adapts gracefully from 1400px down to mobile sizes

## 🔧 **Customization Points**
To modify the canvas size, adjust these key values:
- **Overall Width**: Change `max-width: 1400px` in `.container`
- **Left Panel Width**: Modify `350px` in `grid-template-columns`
- **Height Adjustments**: Update `calc(100vh - XXXpx)` values
- **Minimum Heights**: Adjust `min-height: 400px` values
- **Gaps and Padding**: Modify `gap: 20px` and padding values