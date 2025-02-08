#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

class CompactSystemInfoWithActions(Node):
    def __init__(self):
        super().__init__('compact_system_info_with_actions')

    def extract_info(self):
        # Gather all node names and namespaces
        node_names_and_namespaces = self.get_node_names_and_namespaces()

        print("ROS 2 System Info")
        print("===========================================")

        for (node_name, node_namespace) in node_names_and_namespaces:
            # Skip our own node
            if node_name == self.get_name() and node_namespace == self.get_namespace():
                continue

            # Get published/subscribed topics
            publishers = self.get_publisher_names_and_types_by_node(node_name, node_namespace)
            subscribers = self.get_subscriber_names_and_types_by_node(node_name, node_namespace)

            # Get services
            services = self.get_service_names_and_types_by_node(node_name, node_namespace)

            # Get actions (servers & clients); handle gracefully if not available
            try:
                action_servers = self.get_action_server_names_and_types_by_node(node_name, node_namespace)
            except AttributeError:
                action_servers = []

            try:
                action_clients = self.get_action_client_names_and_types_by_node(node_name, node_namespace)
            except AttributeError:
                action_clients = []

            # Build minimal lists (names only)
            published_topics = [topic_name for (topic_name, _) in publishers]
            subscribed_topics = [topic_name for (topic_name, _) in subscribers]
            service_names = [srv_name for (srv_name, _) in services]
            action_server_names = [act_name for (act_name, _) in action_servers]
            action_client_names = [act_name for (act_name, _) in action_clients]

            # Print minimal node info
            fq_node_name = f"{node_namespace}/{node_name}"
            print(f"\nNode: {fq_node_name}")

            # Publishes
            if published_topics:
                print(f"  Publishes: {', '.join(published_topics)}")

            # Subscribes
            if subscribed_topics:
                print(f"  Subscribes: {', '.join(subscribed_topics)}")

            # Services
            if service_names:
                print(f"  Services: {', '.join(service_names)}")

            # Actions
            if action_server_names or action_client_names:
                print("  Actions:")
                if action_server_names:
                    print(f"    - Action Servers: {', '.join(action_server_names)}")
                else:
                    print("    - Action Servers: None")

                if action_client_names:
                    print(f"    - Action Clients: {', '.join(action_client_names)}")
                else:
                    print("    - Action Clients: None")


def main(args=None):
    rclpy.init(args=args)
    node = CompactSystemInfoWithActions()
    node.extract_info()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
