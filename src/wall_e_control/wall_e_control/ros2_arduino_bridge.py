#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import time

class ArduinoBridge(Node):
    def __init__(self):
        super().__init__('arduino_bridge')
        
        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('max_speed', 100)  # Maximum speed percentage
        
        # Get parameters
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value
        self.max_speed = self.get_parameter('max_speed').value
        
        # Initialize serial connection
        try:
            self.serial = serial.Serial(port, baud, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            self.get_logger().info(f'Connected to Arduino on {port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to connect to Arduino: {e}')
            raise
        
        # Subscribe to cmd_vel
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10)
        
        self.get_logger().info('Arduino bridge node started')
    
    def cmd_vel_callback(self, msg):
        """
        Convert Twist message to Arduino serial commands
        msg.linear.x: forward/backward velocity (-1.0 to 1.0)
        msg.angular.z: rotation velocity (-1.0 to 1.0)
        """
        
        # Scale velocities to percentage (-100 to 100)
        linear = int(msg.linear.x * self.max_speed)
        angular = int(msg.angular.z * self.max_speed)
        
        # Clamp values
        linear = max(-100, min(100, linear))
        angular = max(-100, min(100, angular))
        
        # Send to Arduino
        # Y = forward/backward (moveValue)
        # X = left/right turn (turnValue)
        try:
            self.serial.write(f'Y{linear}\n'.encode())
            time.sleep(0.01)  # Small delay between commands
            self.serial.write(f'X{angular}\n'.encode())
            
            self.get_logger().debug(f'Sent: Y{linear}, X{angular}')
            
        except serial.SerialException as e:
            self.get_logger().error(f'Serial write error: {e}')
    
    def destroy_node(self):
        """Clean up on shutdown"""
        # Stop the robot
        try:
            self.serial.write(b'Y0\n')
            self.serial.write(b'X0\n')
            self.serial.close()
        except:
            pass
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = ArduinoBridge()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()