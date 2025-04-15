# DBN FaUX_GaZe + Gesture Demo

See how interaction intent probabilities propagate with changing inputs over time frames.
Mouse-hover simulated gaze, webcam for recognizing gesture.

## Installation

### Using Conda 

```bash
# Create conda environment
conda create -n cmis-dbn-demo python=3.9 -y
conda activate cmis-dbn-demo

# Install dependencies
pip install -r requirements.txt
```

## Run

```bash
python3 run_gaze_and_gesture_dbn.py
```

### Inputs
Use mouse hover (over objects) to simulate gaze contact. 

Use the following in front of web cam for gesture input:
- index finger up = press down (i.e., analogous to pressing down on a button)
- moving hand left while pinching (index finger and thumb) = swipe left
- moving hand right while pinching = swipe right
- moving hand up while pinching = swipe up
- moving hand down while pinching = swipe down

### Controls
press "q" on keyboard to quit application
