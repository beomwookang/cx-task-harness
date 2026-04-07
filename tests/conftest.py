"""Shared test fixtures for cx-task-harness."""

import pytest


@pytest.fixture
def minimal_task_spec_dict() -> dict:
    """Minimal valid TaskSpec as a Python dict."""
    return {
        "id": "test-task",
        "name": "Test Task",
        "description": "A minimal test task",
        "trigger": {
            "intent": "test intent",
        },
        "steps": [
            {
                "id": "step_1",
                "name": "Greet",
                "type": "message",
                "message_content": "Hello!",
            }
        ],
    }


@pytest.fixture
def order_cancel_task_spec_dict() -> dict:
    """Order cancellation TaskSpec with multiple step types."""
    return {
        "id": "ecommerce-order-cancel",
        "name": "Order Cancellation",
        "description": "Handle order cancellation requests",
        "industry": "ecommerce",
        "trigger": {
            "intent": "Customer wants to cancel an order",
            "keywords": ["cancel", "cancellation", "cancel order"],
        },
        "memory": [
            {"key": "order_id", "type": "string", "description": "The order ID to cancel"},
            {"key": "cancel_reason", "type": "string", "description": "Reason for cancellation"},
        ],
        "steps": [
            {
                "id": "greet_and_collect",
                "name": "Greet and Collect Order Info",
                "type": "agent",
                "instructions": {
                    "role": "Friendly customer support agent for order cancellations",
                    "conversation_flow": [
                        "Greet the customer",
                        "Ask for the order ID",
                        "Ask for the reason for cancellation",
                    ],
                    "exit_conditions": [
                        "Order ID and cancellation reason are collected",
                    ],
                    "exceptions": [
                        "If customer does not know order ID, ask for email to look up",
                    ],
                },
                "next_step": "check_order",
            },
            {
                "id": "check_order",
                "name": "Check Order Status",
                "type": "function",
                "function_url": "https://api.example.com/orders/{{order_id}}",
                "function_method": "GET",
                "function_headers": {"Authorization": "Bearer {{api_key}}"},
                "next_step": "branch_cancelable",
                "on_failure": "error_handler",
            },
            {
                "id": "branch_cancelable",
                "name": "Check if Cancelable",
                "type": "branch",
                "branches": [
                    {
                        "condition": "Order is cancelable",
                        "variable": "order_status",
                        "operator": "in",
                        "value": "pending,processing",
                        "next_step": "cancel_order",
                    },
                    {
                        "condition": "Order already shipped",
                        "variable": "order_status",
                        "operator": "eq",
                        "value": "shipped",
                        "next_step": "shipped_message",
                    },
                ],
                "default_branch": "error_handler",
            },
            {
                "id": "cancel_order",
                "name": "Execute Cancellation",
                "type": "function",
                "function_url": "https://api.example.com/orders/{{order_id}}/cancel",
                "function_method": "POST",
                "function_body": {"reason": "{{cancel_reason}}"},
                "next_step": "confirm_message",
                "on_failure": "error_handler",
            },
            {
                "id": "confirm_message",
                "name": "Confirm Cancellation",
                "type": "message",
                "message_content": "Your order {{order_id}} has been successfully cancelled. A refund will be processed within 3-5 business days.",
                "next_step": "close_action",
            },
            {
                "id": "shipped_message",
                "name": "Already Shipped Notice",
                "type": "message",
                "message_content": "Your order {{order_id}} has already been shipped and cannot be cancelled. Would you like to initiate a return instead?",
                "next_step": "assign_to_human",
            },
            {
                "id": "close_action",
                "name": "Close Conversation",
                "type": "action",
                "action_type": "close",
                "action_params": {"tags": ["order-cancelled", "automated"]},
            },
            {
                "id": "assign_to_human",
                "name": "Assign to Human Agent",
                "type": "action",
                "action_type": "assign_team",
                "action_params": {"team": "returns-team"},
            },
            {
                "id": "error_handler",
                "name": "Error Handler",
                "type": "message",
                "message_content": "I'm sorry, I encountered an issue processing your request. Let me connect you with a human agent.",
                "next_step": "assign_to_human",
            },
        ],
    }
