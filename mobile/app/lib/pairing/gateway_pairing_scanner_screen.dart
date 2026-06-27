import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import 'gateway_pairing.dart';

class GatewayPairingScannerScreen extends StatefulWidget {
  const GatewayPairingScannerScreen({super.key});

  @override
  State<GatewayPairingScannerScreen> createState() =>
      _GatewayPairingScannerScreenState();
}

class _GatewayPairingScannerScreenState
    extends State<GatewayPairingScannerScreen> {
  final MobileScannerController _controller = MobileScannerController(
    formats: const [BarcodeFormat.qrCode],
  );
  bool _handled = false;
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _handleDetect(BarcodeCapture capture) {
    if (_handled) {
      return;
    }
    final barcodes = capture.barcodes;
    if (barcodes.isEmpty) {
      return;
    }
    final raw = barcodes.first.rawValue?.trim();
    if (raw == null || raw.isEmpty) {
      return;
    }
    try {
      final pairing = GatewayPairingPayload.fromQrText(raw);
      _handled = true;
      Navigator.of(context).pop(pairing);
    } on FormatException catch (error) {
      setState(() {
        _error = error.message;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Scan Pairing QR')),
      body: Stack(
        fit: StackFit.expand,
        children: [
          MobileScanner(controller: _controller, onDetect: _handleDetect),
          Align(
            alignment: Alignment.topCenter,
            child: SafeArea(
              child: Container(
                margin: const EdgeInsets.all(16),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: colorScheme.surface.withValues(alpha: 0.92),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _error ?? 'Scan the CCB mobile pairing QR code',
                  key: const ValueKey('gateway-pairing-scan-status'),
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ),
            ),
          ),
          Center(
            child: IgnorePointer(
              child: Container(
                width: 260,
                height: 260,
                decoration: BoxDecoration(
                  border: Border.all(color: colorScheme.primary, width: 3),
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
