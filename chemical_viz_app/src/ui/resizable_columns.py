"""
Resizable columns component for Streamlit using JavaScript.
Allows users to drag column dividers to resize columns dynamically.
"""

import streamlit as st
import streamlit.components.v1 as components
from typing import List, Optional


class ResizableColumns:
    """
    Create resizable columns in Streamlit using draggable dividers.
    """
    
    @staticmethod
    def render_resizable_columns(num_columns: int, initial_widths: Optional[List[int]] = None) -> None:
        """
        Render JavaScript that makes Streamlit columns resizable by dragging.
        
        Args:
            num_columns: Number of columns (2 or 3)
            initial_widths: Initial width ratios for columns
        """
        
        # Generate unique container ID for this instance
        container_id = f"resizable-container-{id(st)}"
        
        # Default widths if not provided
        if initial_widths is None:
            if num_columns == 2:
                initial_widths = [3, 1]
            else:
                initial_widths = [2, 1, 1]
        
        # Normalize widths to percentages
        total_width = sum(initial_widths)
        width_percentages = [w / total_width * 100 for w in initial_widths]
        
        # JavaScript for making columns resizable
        resize_script = f"""
        <style>
            /* Resizable column styles */
            .column-resize-handle {{
                position: absolute;
                top: 0;
                width: 16px;
                height: 100vh;
                cursor: col-resize;
                z-index: 999;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-left: -8px;
            }}
            
            .column-resize-handle::before {{
                content: '';
                width: 4px;
                height: 60px;
                background: #e0e0e0;
                border-radius: 2px;
                transition: all 0.2s ease;
            }}
            
            .column-resize-handle:hover::before {{
                background: #007bff;
                height: 100px;
                width: 6px;
            }}
            
            .column-resize-handle:active::before {{
                background: #0056b3;
            }}
            
            /* Overlay during resize */
            .resize-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 998;
                cursor: col-resize;
                display: none;
            }}
            
            .resize-overlay.active {{
                display: block;
            }}
            
            /* Disable text selection during resize */
            body.resizing {{
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                cursor: col-resize !important;
            }}
            
            body.resizing * {{
                cursor: col-resize !important;
            }}
        </style>
        
        <script>
        (function() {{
            let resizeInitialized = false;
            
            const initResize = () => {{
                if (resizeInitialized) return;
                
                // Find columns - Streamlit uses data-testid="column"
                const columns = document.querySelectorAll('[data-testid="column"]');
                if (columns.length !== {num_columns}) {{
                    // Columns not ready yet, retry
                    setTimeout(initResize, 100);
                    return;
                }}
                
                // Get the parent container
                const parentContainer = columns[0].parentElement;
                if (!parentContainer) return;
                
                // Mark as initialized
                resizeInitialized = true;
                
                // Create overlay for smooth resizing
                const overlay = document.createElement('div');
                overlay.className = 'resize-overlay';
                document.body.appendChild(overlay);
                
                // Set parent container to relative position
                parentContainer.style.position = 'relative';
                
                // Apply initial widths
                const widths = {width_percentages};
                columns.forEach((col, idx) => {{
                    col.style.flex = `0 0 ${{widths[idx]}}%`;
                    col.style.maxWidth = `${{widths[idx]}}%`;
                    col.style.minWidth = '10%';
                    col.style.transition = 'none';
                }});
                
                // Create resize handles
                for (let i = 0; i < {num_columns - 1}; i++) {{
                    const handle = document.createElement('div');
                    handle.className = 'column-resize-handle';
                    
                    let isResizing = false;
                    let startX = 0;
                    let startWidths = [];
                    let currentWidths = [...widths];
                    
                    // Position handle
                    const updateHandlePosition = () => {{
                        const leftOffset = currentWidths.slice(0, i + 1).reduce((a, b) => a + b, 0);
                        handle.style.left = `${{leftOffset}}%`;
                    }};
                    updateHandlePosition();
                    
                    handle.addEventListener('mousedown', (e) => {{
                        isResizing = true;
                        startX = e.pageX;
                        startWidths = [...currentWidths];
                        
                        overlay.classList.add('active');
                        document.body.classList.add('resizing');
                        
                        e.preventDefault();
                        e.stopPropagation();
                    }});
                    
                    const handleMouseMove = (e) => {{
                        if (!isResizing) return;
                        
                        const deltaX = e.pageX - startX;
                        const containerWidth = parentContainer.getBoundingClientRect().width;
                        const deltaPercent = (deltaX / containerWidth) * 100;
                        
                        // Calculate new widths
                        const newWidths = [...startWidths];
                        newWidths[i] += deltaPercent;
                        newWidths[i + 1] -= deltaPercent;
                        
                        // Apply constraints (minimum 15% width, maximum 85%)
                        if (newWidths[i] >= 15 && newWidths[i] <= 85 && 
                            newWidths[i + 1] >= 15 && newWidths[i + 1] <= 85) {{
                            
                            // Update column widths
                            columns[i].style.flex = `0 0 ${{newWidths[i]}}%`;
                            columns[i].style.maxWidth = `${{newWidths[i]}}%`;
                            columns[i + 1].style.flex = `0 0 ${{newWidths[i + 1]}}%`;
                            columns[i + 1].style.maxWidth = `${{newWidths[i + 1]}}%`;
                            
                            currentWidths = newWidths;
                            updateHandlePosition();
                            
                            // Update session state (convert to ratio scale)
                            if ({num_columns} === 2) {{
                                const ratio1 = Math.round(newWidths[0] / 16.67); // 100/6 ≈ 16.67
                                const ratio2 = 6 - ratio1;
                                if (ratio1 >= 1 && ratio1 <= 5) {{
                                    // Update the slider value
                                    const slider = window.parent.document.querySelector('[data-testid="stSlider"] input[type="range"]');
                                    if (slider) {{
                                        slider.value = ratio1;
                                        slider.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        slider.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    }}
                                }}
                            }}
                        }}
                    }};
                    
                    const handleMouseUp = () => {{
                        if (!isResizing) return;
                        
                        isResizing = false;
                        overlay.classList.remove('active');
                        document.body.classList.remove('resizing');
                    }};
                    
                    document.addEventListener('mousemove', handleMouseMove);
                    document.addEventListener('mouseup', handleMouseUp);
                    
                    parentContainer.appendChild(handle);
                }}
            }};
            
            // Start initialization
            initResize();
            
            // Also reinitialize on window resize
            let resizeTimeout;
            window.addEventListener('resize', () => {{
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {{
                    resizeInitialized = false;
                    initResize();
                }}, 250);
            }});
        }})();
        </script>
        """
        
        # Render the script
        components.html(resize_script, height=0)
    
