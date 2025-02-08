import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry


class EncoderTestNode(Node):

    def __init__(self):
        # Initialize the ROS2 node with the name 'encoder_test_node'
        super().__init__('encoder_test_node')

        # Create a publisher for the '/cmd_vel' topic. This will send movement commands.
        # We're using Twist messages to specify velocity.
        self.velocity_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # Create a subscription to the '/vel' topic. This topic provides feedback about the robot's movement.
        # We're using Twist messages to receive velocity data.
        self.velocity_subscription = self.create_subscription(
            Odometry,
            '/vel',
            self.velocity_callback,
            10)
        
        # Initialize a Twist message to set initially zero velocities
        self.move_cmd = Twist()

        # Define initial states
        self.forward = True  # State to decide direction of movement
        self.stop_counter = 0  # Counter to ensure robot stops before changing direction
        
        # Create a timer to periodically call the 'move_robot()' function.
        # This determines how often we check and update movement commands.
        self.timer = self.create_timer(1.0, self.move_robot)

    def velocity_callback(self, msg):
        # This callback function processes the Twist messages received from '/vel'.
        # msg is the message containing the current velocity of the robot.
        
        # For demonstration, we'll just print the robot's current linear and angular velocities.
        self.get_logger().info(f"Current Linear Velocity: {msg.twist.twist.linear.x}, Angular Velocity: {msg.twist.twist.angular.z}")

    def move_robot(self):
        # Alternate the movement direction of the robot back and forth

        if self.stop_counter == 0:
            # Set the -- linear velocity -- to move the robot forward or backward.
            # Forward motion will have a positive linear x velocity.
            # Backward motion will have a negative linear x velocity.
            self.move_cmd.linear.x = 1.0 if self.forward else -1.0

            # Set the -- angular velocity -- to zero as we don't want any rotation here.
            self.move_cmd.angular.z = 0.0

            # Alternate forward direction on each call
            self.forward = not self.forward
            
            # Set the stop counter so that robot will stop in the next cycle
            # This allows the encoders to read zero velocity at each direction change
            self.stop_counter = 3
        else:
            # To pause before changing direction, set velocities to zero
            self.move_cmd.linear.x = 0.0
            self.move_cmd.angular.z = 0.0
            self.stop_counter -= 1

        # Publish the velocity command to '/cmd_vel'
        self.velocity_publisher.publish(self.move_cmd)

        # Informative log about the current movement command sent to the robot
        self.get_logger().info(f"Commanded Linear Velocity: {self.move_cmd.linear.x}")

def main(args=None):
    # Initialize the ROS2 Python client library
    rclpy.init(args=args)

    # Create an instance of our custom node
    encoder_test_node = EncoderTestNode()

    # Execute the node by spinning (processing) callbacks
    rclpy.spin(encoder_test_node)

    # Shutdown the node upon completion
    encoder_test_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()