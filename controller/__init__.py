"""Expose the health and client blueprints registered by the application."""

from controller import actuator_controller, client_controller

blueprints = [actuator_controller.blueprint,
              client_controller.blueprint]
