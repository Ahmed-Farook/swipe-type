import os
import subprocess
import AppKit

def create_mac_icon():
    iconset_dir = "/tmp/AppIcon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)
    
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    
    for s in sizes:
        img = AppKit.NSImage.alloc().initWithSize_(AppKit.NSMakeSize(s, s))
        img.lockFocus()
        
        # 1. Background squircle
        rect = AppKit.NSMakeRect(0, 0, s, s)
        corner = s * 0.22
        path = AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, corner, corner)
        
        # Dark modern gradient
        start_color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.10, 0.12, 0.18, 1.0)
        end_color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.18, 0.22, 0.32, 1.0)
        gradient = AppKit.NSGradient.alloc().initWithStartingColor_endingColor_(start_color, end_color)
        gradient.drawInBezierPath_angle_(path, 90.0)
        
        # Sleek border
        border_color = AppKit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.3, 0.5, 0.9, 0.6)
        border_color.setStroke()
        path.setLineWidth_(max(1.0, s * 0.02))
        path.stroke()
        
        # 2. Draw Keyboard emoji or symbol in center
        font_size = s * 0.52
        font = AppKit.NSFont.systemFontOfSize_(font_size)
        attrs = {
            AppKit.NSFontAttributeName: font,
        }
        string = AppKit.NSAttributedString.alloc().initWithString_attributes_("⌨️", attrs)
        str_size = string.size()
        str_rect = AppKit.NSMakeRect(
            (s - str_size.width) / 2.0,
            (s - str_size.height) / 2.0,
            str_size.width,
            str_size.height
        )
        string.drawInRect_(str_rect)
        
        img.unlockFocus()
        
        rep = AppKit.NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
        png_data = rep.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG, None)
        
        if s == 16:
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_16x16.png", True)
        elif s == 32:
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_16x16@2x.png", True)
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_32x32.png", True)
        elif s == 64:
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_32x32@2x.png", True)
        elif s == 128:
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_128x128.png", True)
        elif s == 256:
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_128x128@2x.png", True)
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_256x256.png", True)
        elif s == 512:
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_256x256@2x.png", True)
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_512x512.png", True)
        elif s == 1024:
            png_data.writeToFile_atomically_(f"{iconset_dir}/icon_512x512@2x.png", True)
            
    # Compile with iconutil
    icns_path = "/Users/ahmed/Desktop/laptop-swipe/AppIcon.icns"
    subprocess.run(["iconutil", "-c", "icns", iconset_dir, "-o", icns_path], check=True)
    print(f"Generated native icon: {icns_path}")

if __name__ == "__main__":
    create_mac_icon()
