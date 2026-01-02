import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# Create figure and 3D axis
fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection='3d')

# Time parameters
t = np.linspace(0, 4*np.pi, 200)

# Aircraft 1 trajectory (pursuing)
x1 = 30 * np.cos(t)
y1 = 30 * np.sin(t)
z1 = 5 * np.sin(2*t) + 20

# Aircraft 2 trajectory (evading)
x2 = 25 * np.cos(t + np.pi/4) + 10 * np.sin(3*t)
y2 = 25 * np.sin(t + np.pi/4) + 10 * np.cos(3*t)
z2 = 8 * np.cos(2*t) + 25

# Initialize plot elements
line1, = ax.plot([], [], [], 'r-', linewidth=2, alpha=0.6, label='Aircraft 1')
line2, = ax.plot([], [], [], 'b-', linewidth=2, alpha=0.6, label='Aircraft 2')
point1, = ax.plot([], [], [], 'ro', markersize=10)
point2, = ax.plot([], [], [], 'bo', markersize=10)

# Set axis limits
ax.set_xlim([-40, 40])
ax.set_ylim([-40, 40])
ax.set_zlim([0, 40])
ax.set_xlabel('X (km)')
ax.set_ylabel('Y (km)')
ax.set_zlabel('Altitude (km)')
ax.set_title('Aircraft Dogfight Simulation', fontsize=14, fontweight='bold')
ax.legend()

# Add grid
ax.grid(True, alpha=0.3)

def init():
    line1.set_data([], [])
    line1.set_3d_properties([])
    line2.set_data([], [])
    line2.set_3d_properties([])
    point1.set_data([], [])
    point1.set_3d_properties([])
    point2.set_data([], [])
    point2.set_3d_properties([])
    return line1, line2, point1, point2

def update(frame):
    # Trail length
    trail_length = 30
    start_idx = max(0, frame - trail_length)
    
    # Update trails
    line1.set_data(x1[start_idx:frame], y1[start_idx:frame])
    line1.set_3d_properties(z1[start_idx:frame])
    
    line2.set_data(x2[start_idx:frame], y2[start_idx:frame])
    line2.set_3d_properties(z2[start_idx:frame])
    
    # Update current positions
    if frame > 0:
        point1.set_data([x1[frame-1]], [y1[frame-1]])
        point1.set_3d_properties([z1[frame-1]])
        
        point2.set_data([x2[frame-1]], [y2[frame-1]])
        point2.set_3d_properties([z2[frame-1]])
    
    # Rotate view slightly for dynamic effect
    ax.view_init(elev=20, azim=frame*0.5)
    
    return line1, line2, point1, point2

# Create animation
anim = FuncAnimation(fig, update, init_func=init, frames=len(t), 
                    interval=50, blit=True, repeat=True)

plt.tight_layout()
plt.show()