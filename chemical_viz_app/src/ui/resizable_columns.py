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
            .resize-handle {{
                position: absolute;
                top: 0;
                width: 10px;
                height: 100%;
                cursor: col-resize;
                background: transparent;
                z-index: 1000;
                transition: background-color 0.2s;
            }}
            
            .resize-handle:hover {{
                background-color: rgba(0, 123, 255, 0.3);
            }}
            
            .resize-handle:active {{
                background-color: rgba(0, 123, 255, 0.5);
            }}
            
            /* Visual indicator during drag */
            .resize-handle::after {{
                content: '';
                position: absolute;
                left: 50%;
                top: 50%;
                transform: translate(-50%, -50%);
                width: 2px;
                height: 40px;
                background-color: #007bff;
                opacity: 0;
                transition: opacity 0.2s;
            }}
            
            .resize-handle:hover::after {{
                opacity: 1;
            }}
            
            /* Disable text selection during resize */
            .resizing {{
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }}
        </style>
        
        <script>
        (function() {{
            // Wait for Streamlit to render columns
            const initResize = () => {{
                // Find the main container with columns
                const containers = document.querySelectorAll('[data-testid="column"]');
                if (containers.length < {num_columns}) {{
                    // Columns not ready yet, retry
                    setTimeout(initResize, 100);
                    return;
                }}
                
                // Get parent container
                const parentContainer = containers[0].parentElement;
                if (!parentContainer) return;
                
                // Set initial widths
                const widths = {width_percentages};
                containers.forEach((col, idx) => {{
                    if (idx < widths.length) {{
                        col.style.flex = `0 0 ${{widths[idx]}}%`;
                        col.style.maxWidth = `${{widths[idx]}}%`;
                    }}
                }});
                
                // Create resize handles between columns
                for (let i = 0; i < {num_columns - 1}; i++) {{
                    const handle = document.createElement('div');
                    handle.className = 'resize-handle';
                    handle.style.left = `${{widths.slice(0, i + 1).reduce((a, b) => a + b, 0)}}%`;
                    
                    let isResizing = false;
                    let startX = 0;
                    let startWidths = [];
                    
                    handle.addEventListener('mousedown', (e) => {{
                        isResizing = true;
                        startX = e.clientX;
                        startWidths = Array.from(containers).map(col => 
                            parseFloat(col.style.flex.split(' ')[2]) || 33.33
                        );
                        
                        document.body.classList.add('resizing');
                        e.preventDefault();
                    }});
                    
                    document.addEventListener('mousemove', (e) => {{
                        if (!isResizing) return;
                        
                        const deltaX = e.clientX - startX;
                        const containerWidth = parentContainer.offsetWidth;
                        const deltaPercent = (deltaX / containerWidth) * 100;
                        
                        // Calculate new widths
                        const newWidths = [...startWidths];
                        newWidths[i] += deltaPercent;
                        newWidths[i + 1] -= deltaPercent;
                        
                        // Apply constraints (minimum 10% width)
                        if (newWidths[i] >= 10 && newWidths[i + 1] >= 10) {{
                            containers[i].style.flex = `0 0 ${{newWidths[i]}}%`;
                            containers[i].style.maxWidth = `${{newWidths[i]}}%`;
                            containers[i + 1].style.flex = `0 0 ${{newWidths[i + 1]}}%`;
                            containers[i + 1].style.maxWidth = `${{newWidths[i + 1]}}%`;
                            
                            // Update handle position
                            handle.style.left = `${{newWidths.slice(0, i + 1).reduce((a, b) => a + b, 0)}}%`;
                            
                            // Store new widths in session state
                            const widthRatios = newWidths.map(w => Math.round(w / 20)); // Convert to 1-5 scale
                            window.parent.postMessage({{
                                type: 'column_resize',
                                widths: widthRatios
                            }}, '*');
                        }}
                    }});
                    
                    document.addEventListener('mouseup', () => {{
                        isResizing = false;
                        document.body.classList.remove('resizing');
                    }});
                    
                    // Add handle to parent container
                    parentContainer.style.position = 'relative';
                    parentContainer.appendChild(handle);
                }}
            }};
            
            // Initialize when DOM is ready
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', initResize);
            }} else {{
                initResize();
            }}
        }})();
        </script>
        """
        
        # Render the script
        components.html(resize_script, height=0)
    
    @staticmethod
    def create_column_listener() -> None:
        """
        Create a listener for column resize events to update session state.
        """
        listener_script = """
        <script>
        window.addEventListener('message', function(event) {
            if (event.data && event.data.type === 'column_resize') {
                // Send the new widths back to Streamlit
                const widths = event.data.widths;
                
                // Find and click a hidden button to update session state
                const button = document.querySelector('[data-testid="update-column-widths"]');
                if (button) {
                    // Store widths in a hidden element first
                    const storage = document.getElementById('column-width-storage');
                    if (storage) {
                        storage.value = JSON.stringify(widths);
                    }
                    button.click();
                }
            }
        });
        </script>
        """
        
        components.html(listener_script, height=0)