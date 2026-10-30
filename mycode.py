# calling libraries
from netmiko import ConnectHandler
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox, QMessageBox, QGroupBox, QGridLayout, QVBoxLayout, QHBoxLayout
import sys
import time
import os
import json
from datetime import datetime


# get the same folder where this python code exists
# i used this because i want the files to be saved beside the code file not in another place
base_dir = os.path.dirname(os.path.abspath(__file__))

# file to save the last ip for each router
ip_file = os.path.join(base_dir, "router_ips.json")

# file to save some information about routers
info_file = os.path.join(base_dir, "router_info.txt")


# dictionary of routers with their connection settings
routers = {
    "R1": {
        "device_type": "cisco_ios",
        "host": "192.168.85.201",
        "username": "admin",
        "password": "admin",
        "secret": "admin",
        "use_keys": False,  # we set this to tell netmiko to use password & username only for router connection
        "allow_agent": False,  # that command tell netmiko to not use ssh keys because there's some devices has ssh agent saved on it
        "ssh_config_file": None,  # that also tell netmiko to not use ssh files from system
        "disabled_algorithms": {"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},  # that to solve configuration issue with cisco old routers
        "conn_timeout": 20,  # waiting time to call if the router doesn't respond in 20s time out
    },
    "R2": {
        "device_type": "cisco_ios",
        "host": "172.16.0.2",
        "username": "admin",
        "password": "admin",
        "secret": "admin",
        "use_keys": False,  # we set this to tell netmiko to use password & username only for router connection
        "allow_agent": False,  # that command tell netmiko to not use ssh keys because there's some devices has ssh agent saved on it
        "ssh_config_file": None,  # that also tell netmiko to not use ssh files from system
        "disabled_algorithms": {"pubkeys": ["rsa-sha2-256", "rsa-sha2-512"]},  # that to solve configuration issue with cisco old routers
        "conn_timeout": 20,  # waiting time to call if the router doesn't respond in 20s time out
    }
}


# load saved router IPs if the file already exists
# i used this because if i change router ip i don't need to edit the code every time
if os.path.exists(ip_file):
    with open(ip_file, "r") as f:
        saved_ips = json.load(f)

    for name in saved_ips:
        if name in routers:
            routers[name]["host"] = saved_ips[name]


class RouterGUI(QWidget):
    def __init__(self):
        super().__init__()

        # this variable will hold the connection after connect button is pressed
        self.net_connect = None

        # this variable will hold the selected router name
        self.current_router_name = None

        # basic window settings
        self.setWindowTitle("Router Automation GUI")
        self.setGeometry(200, 100, 950, 750)

        # call function that creates the gui design
        self.create_gui()

        # show where files are saved
        self.show_output("Files will be saved in this folder:")
        self.show_output(base_dir)
        self.show_output("Select router and press Connect.")

    # this function creates the gui design
    # i put all labels, buttons, textboxes here to keep the code organized
    def create_gui(self):
        main_layout = QVBoxLayout()

        title_label = QLabel("Router Automation GUI")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # router connection group
        connection_group = QGroupBox("Router Connection")
        connection_layout = QGridLayout()

        self.router_combo = QComboBox()
        self.router_combo.addItem("R1")
        self.router_combo.addItem("R2")

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_button_action)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_router)

        self.r1_ip_label = QLabel("R1 IP: " + routers["R1"]["host"])
        self.r2_ip_label = QLabel("R2 IP: " + routers["R2"]["host"])
        self.status_label = QLabel("Status: Not Connected")

        connection_layout.addWidget(QLabel("Select Router:"), 0, 0)
        connection_layout.addWidget(self.router_combo, 0, 1)
        connection_layout.addWidget(self.connect_button, 0, 2)
        connection_layout.addWidget(self.disconnect_button, 0, 3)
        connection_layout.addWidget(self.r1_ip_label, 1, 0, 1, 2)
        connection_layout.addWidget(self.r2_ip_label, 1, 2, 1, 2)
        connection_layout.addWidget(self.status_label, 2, 0, 1, 4)

        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)

        # change interface ip group
        ip_group = QGroupBox("Change Interface IP")
        ip_layout = QGridLayout()

        self.interface_entry = QLineEdit()
        self.interface_entry.setText("FastEthernet0/0")

        self.new_ip_entry = QLineEdit()

        self.mask_entry = QLineEdit()
        self.mask_entry.setText("255.255.255.0")

        self.change_ip_button = QPushButton("Change IP")
        self.change_ip_button.clicked.connect(self.change_interface_ip)

        ip_layout.addWidget(QLabel("Interface:"), 0, 0)
        ip_layout.addWidget(self.interface_entry, 0, 1)
        ip_layout.addWidget(QLabel("New IP:"), 0, 2)
        ip_layout.addWidget(self.new_ip_entry, 0, 3)
        ip_layout.addWidget(QLabel("Mask:"), 0, 4)
        ip_layout.addWidget(self.mask_entry, 0, 5)
        ip_layout.addWidget(self.change_ip_button, 0, 6)

        ip_group.setLayout(ip_layout)
        main_layout.addWidget(ip_group)

        # static route group
        route_group = QGroupBox("Add Static Route")
        route_layout = QGridLayout()

        self.network_entry = QLineEdit()
        self.route_mask_entry = QLineEdit()
        self.nexthop_entry = QLineEdit()

        self.route_button = QPushButton("Add Route")
        self.route_button.clicked.connect(self.add_static_route)

        route_layout.addWidget(QLabel("Network:"), 0, 0)
        route_layout.addWidget(self.network_entry, 0, 1)
        route_layout.addWidget(QLabel("Mask:"), 0, 2)
        route_layout.addWidget(self.route_mask_entry, 0, 3)
        route_layout.addWidget(QLabel("Next Hop:"), 0, 4)
        route_layout.addWidget(self.nexthop_entry, 0, 5)
        route_layout.addWidget(self.route_button, 0, 6)

        route_group.setLayout(route_layout)
        main_layout.addWidget(route_group)

        # ospf group
        ospf_group = QGroupBox("Configure OSPF")
        ospf_layout = QGridLayout()

        self.ospf_pid_entry = QLineEdit()
        self.ospf_pid_entry.setText("1")

        self.ospf_network_entry = QLineEdit()
        self.wildcard_entry = QLineEdit()

        self.area_entry = QLineEdit()
        self.area_entry.setText("0")

        self.ospf_button = QPushButton("Configure OSPF")
        self.ospf_button.clicked.connect(self.configure_ospf)

        ospf_layout.addWidget(QLabel("Process ID:"), 0, 0)
        ospf_layout.addWidget(self.ospf_pid_entry, 0, 1)
        ospf_layout.addWidget(QLabel("Network:"), 0, 2)
        ospf_layout.addWidget(self.ospf_network_entry, 0, 3)
        ospf_layout.addWidget(QLabel("Wildcard:"), 0, 4)
        ospf_layout.addWidget(self.wildcard_entry, 0, 5)
        ospf_layout.addWidget(QLabel("Area:"), 0, 6)
        ospf_layout.addWidget(self.area_entry, 0, 7)
        ospf_layout.addWidget(self.ospf_button, 0, 8)

        ospf_group.setLayout(ospf_layout)
        main_layout.addWidget(ospf_group)

        # add user group
        user_group = QGroupBox("Add User")
        user_layout = QGridLayout()

        self.username_entry = QLineEdit()
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.user_button = QPushButton("Add User")
        self.user_button.clicked.connect(self.add_user)

        user_layout.addWidget(QLabel("Username:"), 0, 0)
        user_layout.addWidget(self.username_entry, 0, 1)
        user_layout.addWidget(QLabel("Password:"), 0, 2)
        user_layout.addWidget(self.password_entry, 0, 3)
        user_layout.addWidget(self.user_button, 0, 4)

        user_group.setLayout(user_layout)
        main_layout.addWidget(user_group)

        # general buttons group
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save Config")
        self.save_button.clicked.connect(self.save_config_button)

        self.show_info_button = QPushButton("Show Router Info")
        self.show_info_button.clicked.connect(self.show_router_info)

        self.clear_button = QPushButton("Clear Output")
        self.clear_button.clicked.connect(self.clear_output)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit_program)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.show_info_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.exit_button)

        main_layout.addLayout(button_layout)

        # output box
        # this is where the result of router commands will appear
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        main_layout.addWidget(self.output_box)

        self.setLayout(main_layout)

    # this function prints text inside the output box in the gui
    # i made it instead of print because in gui the user should see output inside the program window
    def show_output(self, text):
        self.output_box.append(str(text))

    # this function clears the output box
    # i added this to make the screen clean when i want
    def clear_output(self):
        self.output_box.clear()

    # this function saves router ips in json file
    # so when i open the program again it will use the last ip
    def save_router_ips(self):
        saved_ips = {}

        for name in routers:
            saved_ips[name] = routers[name]["host"]

        with open(ip_file, "w") as f:
            json.dump(saved_ips, f, indent=4)

    # this function connects to router
    # i made it function because i need to reconnect after changing ip
    def connect_to_router(self, router, router_name):
        self.show_output("Connecting to " + router_name + " (" + router["host"] + ")...")
        connection = ConnectHandler(**router)  # create ssh session
        connection.enable()
        self.show_output("Connected!")
        return connection

    # this function saves router config safely
    # i used write memory because save_config sometimes waits for enter and the program looks like it stopped
    def save_config_safely(self, connection):
        output = connection.send_command_timing("write memory")

        # some routers ask about destination filename
        # here i send enter to accept the default name startup-config
        if "Destination filename" in output:
            output += connection.send_command_timing("\n")

        return output

    # this small function runs show commands and prints the output in gui
    # i made it to avoid repeating try and except many times
    def run_show_command(self, title, command):
        self.show_output("\n--- " + title + " ---")

        try:
            output = self.net_connect.send_command(command)

            if output.strip() == "":
                self.show_output("No output from: " + command)
            else:
                self.show_output(output)

        except Exception as e:
            self.show_output("Could not run: " + command)
            self.show_output("Error: " + str(e))

    # this function shows only ip/interface details
    # i call it only after changing interface ip or when user presses show router info
    def show_ip_details(self):
        self.show_output("\n========== IP / Interface Details ==========")

        self.run_show_command("Interface IP Brief", "show ip interface brief")

        interface = self.interface_entry.text()

        if interface != "":
            self.run_show_command("Selected Interface Details", "show running-config interface " + interface)

        self.show_output("============================================\n")

    # this function shows only static route details
    # i call it only after add static route option
    def show_static_route_details(self):
        self.show_output("\n========== Static Route Details ==========")

        self.run_show_command("Static Routes From Config", "show running-config | include ^ip route")
        self.run_show_command("Routing Table", "show ip route")

        network = self.network_entry.text()

        if network != "":
            self.run_show_command("Route For Entered Network", "show ip route " + network)

        self.show_output("==========================================\n")

    # this function shows only ospf details
    # i call it only after configure ospf option
    def show_ospf_details(self):
        self.show_output("\n========== OSPF Details ==========")

        self.run_show_command("OSPF Neighbors", "show ip ospf neighbor")
        self.run_show_command("OSPF Protocol Information", "show ip protocols")
        self.run_show_command("OSPF Interface Brief", "show ip ospf interface brief")
        self.run_show_command("OSPF Routes", "show ip route ospf")

        self.show_output("==================================\n")

    # this function shows only user details
    # i call it only after add user option
    def show_user_details(self):
        self.show_output("\n========== User Details ==========")

        self.run_show_command("Configured Users", "show running-config | include username")

        self.show_output("==================================\n")

    # this function shows full router details
    # this is only used by show router info button because this button is made to show everything
    def show_all_router_details(self):
        self.show_output("\n========== Full Router Details ==========")
        self.show_output("Router: " + str(self.current_router_name))
        self.show_output("Management IP used by program: " + routers[self.current_router_name]["host"])

        self.run_show_command("Hostname", "show running-config | include hostname")
        self.run_show_command("Interface IP Brief", "show ip interface brief")
        self.run_show_command("Routing Table", "show ip route")
        self.run_show_command("Static Routes", "show running-config | include ^ip route")
        self.run_show_command("OSPF Neighbors", "show ip ospf neighbor")
        self.run_show_command("OSPF Protocol Information", "show ip protocols")
        self.run_show_command("OSPF Interface Brief", "show ip ospf interface brief")
        self.run_show_command("Configured Users", "show running-config | include username")

        self.show_output("=========================================\n")

    # this function saves router information in text file
    # i used it to keep record for router ip and interfaces
    def save_router_info(self, connection, router_name, router_ip):
        try:
            hostname = connection.send_command("show running-config | include hostname")
            interfaces = connection.send_command("show ip interface brief")
            routes = connection.send_command("show ip route")
            static_routes = connection.send_command("show running-config | include ^ip route")
            ospf_neighbors = connection.send_command("show ip ospf neighbor")
            ospf_protocols = connection.send_command("show ip protocols")

            with open(info_file, "a") as f:
                f.write("\n==============================\n")
                f.write("Date: " + str(datetime.now()) + "\n")
                f.write("Router Name: " + router_name + "\n")
                f.write("Router IP: " + router_ip + "\n")

                f.write("\nHostname:\n")
                f.write(hostname + "\n")

                f.write("\nInterface Information:\n")
                f.write(interfaces + "\n")

                f.write("\nRouting Table:\n")
                f.write(routes + "\n")

                f.write("\nStatic Routes:\n")
                f.write(static_routes + "\n")

                f.write("\nOSPF Neighbors:\n")
                f.write(ospf_neighbors + "\n")

                f.write("\nOSPF Protocol Information:\n")
                f.write(ospf_protocols + "\n")

                f.write("==============================\n")

        except Exception as e:
            self.show_output("Could not save router information.")
            self.show_output("Error: " + str(e))

    # this function updates the labels that show router ips
    # i used it because when ip changes the gui should show the new ip
    def update_router_labels(self):
        self.r1_ip_label.setText("R1 IP: " + routers["R1"]["host"])
        self.r2_ip_label.setText("R2 IP: " + routers["R2"]["host"])

    # this function connects when the user presses connect button
    # it takes router name from combo box
    def connect_button_action(self):
        router_name = self.router_combo.currentText()

        if router_name == "":
            QMessageBox.warning(self, "Error", "Please select a router first")
            return

        self.current_router_name = router_name
        router = routers[router_name]

        try:
            self.net_connect = self.connect_to_router(router, router_name)
            self.status_label.setText("Status: Connected to " + router_name)

            # i do not print all router details here
            # because connect button should only connect, not show every command
            self.show_output("Connection is ready. Now choose the option you want.")

        except Exception as e:
            self.show_output("Could not connect to router.")
            self.show_output("Error: " + str(e))

            answer = QMessageBox.question(
                self,
                "Connection Failed",
                "Do you want to try another IP?",
                QMessageBox.Yes | QMessageBox.No
            )

            if answer == QMessageBox.Yes:
                self.manual_ip_window(router_name)

    # this function opens small window to enter another ip
    # i added it because sometimes saved ip is wrong or router ip changed
    def manual_ip_window(self, router_name):
        self.ip_window = QWidget()
        self.ip_window.setWindowTitle("Enter New Router IP")
        self.ip_window.setGeometry(350, 250, 300, 150)

        layout = QVBoxLayout()

        label = QLabel("Enter IP for " + router_name)
        self.manual_ip_entry = QLineEdit()

        button = QPushButton("Connect")
        button.clicked.connect(lambda: self.save_new_manual_ip(router_name))

        layout.addWidget(label)
        layout.addWidget(self.manual_ip_entry)
        layout.addWidget(button)

        self.ip_window.setLayout(layout)
        self.ip_window.show()

    # this function saves the manual ip and tries to connect with it
    # i separated it from manual_ip_window to keep the code easy to read
    def save_new_manual_ip(self, router_name):
        new_ip = self.manual_ip_entry.text()

        if new_ip == "":
            QMessageBox.warning(self, "Error", "Please enter IP address")
            return

        routers[router_name]["host"] = new_ip
        self.save_router_ips()
        self.update_router_labels()

        try:
            self.current_router_name = router_name
            self.net_connect = self.connect_to_router(routers[router_name], router_name)
            self.status_label.setText("Status: Connected to " + router_name)
            self.show_output("New IP saved in: " + ip_file)
            self.show_output("Connection is ready. Now choose the option you want.")
            self.ip_window.close()

        except Exception as e:
            self.show_output("Still could not connect.")
            self.show_output("Error: " + str(e))

    # this function checks if the router is connected before running commands
    # i used it to avoid errors if user presses any button before connect
    def check_connection(self):
        if self.net_connect is None:
            QMessageBox.warning(self, "Error", "Please connect to a router first")
            return False

        return True

    # this function changes interface ip
    # it works like option 1 in the old menu program
    def change_interface_ip(self):
        if self.check_connection() == False:
            return

        interface = self.interface_entry.text()
        new_ip = self.new_ip_entry.text()
        mask = self.mask_entry.text()

        if interface == "" or new_ip == "" or mask == "":
            QMessageBox.warning(self, "Error", "Please fill interface, new ip, and mask")
            return

        router = routers[self.current_router_name]
        old_ip = router["host"]

        # give the router the new ip and subnet mask
        commands = [
            "interface " + interface,
            "ip address " + new_ip + " " + mask,
            "no shutdown"
        ]

        try:
            output = self.net_connect.send_config_set(commands)  # send commands to router
            self.show_output(output)
            self.show_output("IP changed.")

        except Exception:
            # connection will drop here if i changed the same ip that ssh uses
            pass

        self.show_output("Connection may drop.")
        self.show_output("Reconnecting...")

        time.sleep(3)  # wait 3 seconds for router to apply new ip

        try:
            self.net_connect.disconnect()
        except Exception:
            pass

        reconnected = False

        # first try old ip because maybe i changed another interface not the ssh interface
        try:
            router["host"] = old_ip
            self.net_connect = self.connect_to_router(router, self.current_router_name)
            reconnected = True

        except Exception:
            self.show_output("Could not reconnect using old IP: " + old_ip)
            self.show_output("Trying new IP: " + new_ip)

        # if old ip failed then try the new ip
        if reconnected == False:
            try:
                router["host"] = new_ip  # update host to new ip
                self.net_connect = self.connect_to_router(router, self.current_router_name)
                reconnected = True

            except Exception as e:
                self.show_output("Could not reconnect using new IP.")
                self.show_output("Reconnect manually using: " + new_ip)
                self.show_output("Error: " + str(e))
                return

        if reconnected == True:
            self.show_output(self.save_config_safely(self.net_connect))

            routers[self.current_router_name]["host"] = router["host"]
            self.save_router_ips()
            self.update_router_labels()

            self.status_label.setText("Status: Connected to " + self.current_router_name)
            self.show_output("Reconnected and config saved!")
            self.show_output("Router IP saved in: " + ip_file)

            # here i print only ip/interface details because this option is change ip
            self.show_ip_details()

            self.save_router_info(self.net_connect, self.current_router_name, router["host"])
            self.show_output("Router information saved in: " + info_file)

    # this function adds static route
    # it works like option 2 in the old menu program
    def add_static_route(self):
        if self.check_connection() == False:
            return

        network = self.network_entry.text()  # the address of network that want router to access
        mask = self.route_mask_entry.text()  # tell how big the network is
        nexthop = self.nexthop_entry.text()  # ip of the next router

        if network == "" or mask == "" or nexthop == "":
            QMessageBox.warning(self, "Error", "Please fill network, mask, and next hop")
            return

        commands = [
            "ip route " + network + " " + mask + " " + nexthop
        ]

        try:
            output = self.net_connect.send_config_set(commands)
            self.show_output(output)

            self.show_output(self.save_config_safely(self.net_connect))
            self.show_output("Static route added and config saved!")

            # here i print only route details because this option is static route
            self.show_static_route_details()

            self.save_router_info(self.net_connect, self.current_router_name, routers[self.current_router_name]["host"])
            self.show_output("Router information saved in: " + info_file)

        except Exception as e:
            self.show_output("Could not add static route.")
            self.show_output("Error: " + str(e))

    # this function configures ospf
    # it works like option 3 in the old menu program
    def configure_ospf(self):
        if self.check_connection() == False:
            return

        pid = self.ospf_pid_entry.text()
        network = self.ospf_network_entry.text()
        wildcard = self.wildcard_entry.text()
        area = self.area_entry.text()

        if pid == "" or network == "" or wildcard == "" or area == "":
            QMessageBox.warning(self, "Error", "Please fill all OSPF fields")
            return

        commands = [
            "router ospf " + pid,
            "network " + network + " " + wildcard + " area " + area
        ]

        try:
            output = self.net_connect.send_config_set(commands)
            self.show_output(output)

            self.show_output(self.save_config_safely(self.net_connect))
            self.show_output("OSPF configured and config saved!")

            # sometimes ospf neighbor needs few seconds to appear
            time.sleep(2)

            # here i print only ospf details because this option is ospf
            self.show_ospf_details()

            self.save_router_info(self.net_connect, self.current_router_name, routers[self.current_router_name]["host"])
            self.show_output("Router information saved in: " + info_file)

        except Exception as e:
            self.show_output("Could not configure OSPF.")
            self.show_output("Error: " + str(e))

    # this function adds new user to router
    # it works like option 4 in the old menu program
    def add_user(self):
        if self.check_connection() == False:
            return

        username = self.username_entry.text()
        password = self.password_entry.text()

        if username == "" or password == "":
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return

        commands = [
            "username " + username + " privilege 15 secret " + password
        ]

        try:
            output = self.net_connect.send_config_set(commands)
            self.show_output(output)

            self.show_output(self.save_config_safely(self.net_connect))
            self.show_output("User added and config saved!")

            # here i print only user details because this option is add user
            self.show_user_details()

            self.save_router_info(self.net_connect, self.current_router_name, routers[self.current_router_name]["host"])
            self.show_output("Router information saved in: " + info_file)

        except Exception as e:
            self.show_output("Could not add user.")
            self.show_output("Error: " + str(e))

    # this function only saves config
    # it works like option 5 in the old menu program
    def save_config_button(self):
        if self.check_connection() == False:
            return

        try:
            output = self.save_config_safely(self.net_connect)
            self.show_output(output)

            # here i do not print ip, ospf, or route details
            # because save button should only save the configuration
            self.show_output("Config saved!")

            self.save_router_info(self.net_connect, self.current_router_name, routers[self.current_router_name]["host"])
            self.show_output("Router information saved in: " + info_file)

        except Exception as e:
            self.show_output("Could not save config.")
            self.show_output("Error: " + str(e))

    # this function shows router info
    # it is useful to check everything manually if i want
    def show_router_info(self):
        if self.check_connection() == False:
            return

        # this button is the only one that shows full details
        self.show_all_router_details()

        self.save_router_info(self.net_connect, self.current_router_name, routers[self.current_router_name]["host"])
        self.show_output("Router information saved in: " + info_file)

    # this function disconnects from router
    # i added it because in gui there is no exit menu like before
    def disconnect_router(self):
        if self.net_connect is not None:
            try:
                self.net_connect.disconnect()
                self.show_output("Disconnected.")
                self.status_label.setText("Status: Disconnected")
                self.net_connect = None

            except Exception as e:
                self.show_output("Error while disconnecting: " + str(e))
        else:
            self.show_output("No active connection.")

    # this function closes the program
    # before closing it tries to disconnect from router
    def exit_program(self):
        self.disconnect_router()
        self.close()


# run the pyqt5 application
# QApplication is the main object that starts the gui program
app = QApplication(sys.argv)

# create object from RouterGUI class
window = RouterGUI()

# show the window on screen
window.show()

# keep the gui running until user closes it
sys.exit(app.exec_())