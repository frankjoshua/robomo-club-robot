import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator, NavigationResult

class SquarePatternNavigator(Node):

    def __init__(self):
        super().__init__('square_pattern_navigator')
        self.navigator = BasicNavigator()

    def get_square_path(self):
        waypoints = [
            {'x': 0.0, 'y': 0.0, 'theta': 0.0},
            {'x': 0.2, 'y': 0.0, 'theta': 1.57},
            {'x': 0.2, 'y': 0.2, 'theta': 3.14},
            {'x': 0.0, 'y': 0.2, 'theta': -1.57},
            {'x': 0.0, 'y': 0.0, 'theta': 0.0}
        ]
        return waypoints

    def move_in_square(self):
        waypoints = self.get_square_path()
        for waypoint in waypoints:
            self.go_to_position(waypoint)

    def go_to_position(self, waypoint):
        self.navigator.goToPosition(waypoint)
        navigation_result = self.navigator.waitUntilNav2Active()
        self.log_navigation_result(navigation_result, waypoint)

    def log_navigation_result(self, result, waypoint):
        if result != NavigationResult.SUCCEEDED:
            self.get_logger().info(f'Navigation failed at {waypoint}')

def main(args=None):
    rclpy.init(args=args)
    
    square_pattern_navigator = SquarePatternNavigator()
    square_pattern_navigator.move_in_square()
    
    rclpy.shutdown()

if __name__ == '__main__':
    main()
