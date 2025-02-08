from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
import rclpy
from rclpy.node import Node
import time

def create_pose(x, y, theta):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = rclpy.time.Time().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = theta
    return pose

def main():
    rclpy.init()
    node = Node('nav2_square')

    navigator = BasicNavigator()
    navigator.waitUntilNav2Active()

    # Define the square path
    initial_pose = create_pose(0.0, 0.0, 0.0)  # Starting point of the robot
    poses = [
        create_pose(0.5, 0.0, 0.0),  # 0.5 meters right
        create_pose(0.5, 0.5, 0.0),  # 0.5 meters up
        create_pose(0.0, 0.5, 0.0),  # 0.5 meters left
        create_pose(0.0, 0.0, 0.0)   # 0.5 meters down to the start
    ]

    # Set initial pose
    navigator.setInitialPose(initial_pose)
    
    # Execute the square movement
    for pose in poses:
        navigator.goToPose(pose)

        while not navigator.isTaskComplete():
            time.sleep(0.1)  # Sleep for a short duration to simulate continuous checking
            # Optionally get feedback here if needed
            feedback = navigator.getFeedback()
            if feedback.navigation_duration > 600:
                navigator.cancelTask()
                print("Task taking too long, cancelling...")
                return

        result = navigator.getResult()
        if result == navigator.TaskResult.SUCCEEDED:
            print('Reached pose successfully!')
        elif result == navigator.TaskResult.CANCELED:
            print('Goal was canceled!')
            break
        elif result == navigator.TaskResult.FAILED:
            print('Goal failed!')
            break

    print("Square completed")
    navigator.lifecycleShutdown()
    rclpy.shutdown()

if __name__ == '__main__':
    main()