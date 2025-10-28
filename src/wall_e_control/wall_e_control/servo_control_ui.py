#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import serial
import sys
import termios
import tty
import time

class ServoKeyboard(Node):
    def __init__(self):
        super().__init__('servo_control_ui')
        
        # Declare parameters
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('baud_rate', 115200)
        
        # Get parameters
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value
        
        # Initialize serial connection
        try:
            self.serial = serial.Serial(port, baud, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            
            # Clear any startup messages from Arduinomhfkh
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            
            self.get_logger().info(f'Connected to Arduino on {port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to connect to Arduino: {e}')
            raise
        
        # Current servo positions (0-100)
        self.positions = {
            'head_rotation': 50,
            'neck_top': 50,
            'neck_bottom': 50,
            'eye_right': 50,
            'eye_left': 50,
            'arm_left': 50,
            'arm_right': 50
        }
        
        # Servo command mapping (matches Arduino code)
        self.servo_commands = {
            'head_rotation': 'G',
            'neck_top': 'T',
            'neck_bottom': 'B',
            'eye_right': 'U',
            'eye_left': 'E',
            'arm_left': 'L',
            'arm_right': 'R'
        }
        
        self.current_servo = 'head_rotation'
        self.step_size = 5
        
        self.print_instructions()
        self.settings = self.save_terminal_settings()
        
        # Test connection
        self.test_connection()

    def test_connection(self):
        """Test if Arduino is responding"""
        self.get_logger().info("Testing Arduino connection...")
        test_cmd = 'G50\n'
        self.serial.write(test_cmd.encode())
        self.serial.flush()
        time.sleep(0.2)
        
        # Read Arduino's echo
        if self.serial.in_waiting:
            response = self.serial.readline().decode().strip()
            self.get_logger().info(f"Arduino echo: {response}")
        else:
            self.get_logger().warn("No response from Arduino - check connection!")

    def save_terminal_settings(self):
        """Save current terminal settings"""
        return termios.tcgetattr(sys.stdin)

    def restore_terminal_settings(self):
        """Restore terminal settings"""
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)

    def get_key(self):
        """Get a single keypress or escape sequence"""
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        
        # Handle escape sequences (arrow keys)
        if key == '\x1b':
            # Read next two characters
            next_chars = sys.stdin.read(2)
            key = '\x1b' + next_chars
        
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def send_servo_command(self, servo_name):
        """Send servo position to Arduino"""
        command_char = self.servo_commands[servo_name]
        position = self.positions[servo_name]
        command = f'{command_char}{position}\n'
        
        try:
            # Clear input buffer before sending
            self.serial.reset_input_buffer()
            
            # Send command
            self.get_logger().info(f'Sending: {command.strip()}')
            self.serial.write(command.encode())
            self.serial.flush()
            
            # Wait a bit for Arduino to process
            time.sleep(0.05)
            
            # Read Arduino's echo response
            if self.serial.in_waiting:
                response = self.serial.readline().decode().strip()
                self.get_logger().info(f'Arduino: {response}')
            
            self.get_logger().info(f'{servo_name}: {position}%')
            
        except serial.SerialException as e:
            self.get_logger().error(f'Serial error: {e}')

    def print_instructions(self):
        """Print control instructions"""
        print("\n" + "="*60)
        print("     WALL-E SERVO CONTROL - KEYBOARD INTERFACE")
        print("="*60)
        print("\n📋 SERVO SELECTION:")
        print("  1 - Head Rotation")
        print("  2 - Neck Top")
        print("  3 - Neck Bottom")
        print("  4 - Eye Right")
        print("  5 - Eye Left")
        print("  6 - Arm Left")
        print("  7 - Arm Right")
        print("\n🎮 SERVO CONTROL:")
        print("  w - Increase position (+5)")
        print("  s - Decrease position (-5)")
        print("  + / ] - Increase position (+1)")
        print("  - / [ - Decrease position (-1)")
        print("\n🎯 PRESETS:")
        print("  0 - Center all servos (50%)")
        print("  h - Home position")
        print("  r - Reset current servo to 50%")
        print("\n❌ EXIT:")
        print("  q / ESC - Quit")
        print("="*60 + "\n")

    def print_status(self):
        """Print current status"""
        print("\n" + "-"*60)
        print(f"🎯 Current Servo: {self.current_servo.replace('_', ' ').title()}")
        print(f"📊 Position: {self.positions[self.current_servo]}%")
        print("-"*60)
        print("All Positions:")
        for servo, pos in self.positions.items():
            bar = "█" * int(pos/5) + "░" * (20 - int(pos/5))
            print(f"  {servo.replace('_', ' ').title():15s} [{bar}] {pos}%")
        print("-"*60)

    def center_all_servos(self):
        """Set all servos to center position"""
        for servo in self.positions.keys():
            self.positions[servo] = 50
            self.send_servo_command(servo)
            time.sleep(0.15)  # Increased delay between commands
        self.get_logger().info("All servos centered")

    def home_position(self):
        """Move to home position"""
        home_positions = {
            'head_rotation': 50,
            'neck_top': 80,
            'neck_bottom': 20,
            'eye_right': 40,
            'eye_left': 40,
            'arm_left': 50,
            'arm_right': 50
        }
        for servo, pos in home_positions.items():
            self.positions[servo] = pos
            self.send_servo_command(servo)
            time.sleep(0.15)
        self.get_logger().info("Moved to home position")

    def run(self):
        """Main control loop"""
        self.print_status()
        
        try:
            while True:
                key = self.get_key()
                
                # Servo selection (1-7)
                if key in '1234567':
                    servo_list = list(self.positions.keys())
                    self.current_servo = servo_list[int(key) - 1]
                    self.print_status()
                
                # Increase position
                elif key == 'w':
                    self.positions[self.current_servo] = min(100, self.positions[self.current_servo] + self.step_size)
                    self.send_servo_command(self.current_servo)
                    self.print_status()
                
                # Decrease position
                elif key == 's':
                    self.positions[self.current_servo] = max(0, self.positions[self.current_servo] - self.step_size)
                    self.send_servo_command(self.current_servo)
                    self.print_status()
                
                # Fine control - increase
                elif key in ['+', '=', ']']:
                    self.positions[self.current_servo] = min(100, self.positions[self.current_servo] + 1)
                    self.send_servo_command(self.current_servo)
                    self.print_status()
                
                # Fine control - decrease
                elif key in ['-', '_', '[']:
                    self.positions[self.current_servo] = max(0, self.positions[self.current_servo] - 1)
                    self.send_servo_command(self.current_servo)
                    self.print_status()
                
                # Center all servos
                elif key == '0':
                    self.center_all_servos()
                    self.print_status()
                
                # Home position
                elif key == 'h':
                    self.home_position()
                    self.print_status()
                
                # Reset current servo
                elif key == 'r':
                    self.positions[self.current_servo] = 50
                    self.send_servo_command(self.current_servo)
                    self.print_status()
                
                # Help
                elif key == '?':
                    self.print_instructions()
                    self.print_status()
                
                # Quit
                elif key in ['q', 'Q', '\x1b']:
                    print("\n👋 Exiting Wall-E Servo Control...")
                    break
                
        except KeyboardInterrupt:
            print("\n👋 Exiting Wall-E Servo Control...")
        finally:
            self.restore_terminal_settings()
            self.serial.close()

    def destroy_node(self):
        """Clean up"""
        try:
            self.restore_terminal_settings()
            self.serial.close()
        except:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = ServoKeyboard()
        node.run()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()