# MercadoPago Core

This module provides a modular architecture for MercadoPago integration, replacing the legacy `mercadopago_integracion.py`.

## Files:
- `api_client.py`: Provides helper functions for making API requests to MercadoPago.
- `point_service.py`: Handles payments using MercadoPago Point devices.
- `qr_service.py`: Handles dynamic QR code generation and payment processing.
- `polling_service.py`: Handles polling and verification of MercadoPago transfers.
- `ui_dialogs.py`: Contains the UI dialogs for waiting and polling for payments.

## Usage:
Import the respective service class and instantiate it with the parent component to call the needed methods.
