import 'package:flutter/material.dart';

class StatusBadge extends StatelessWidget {
  final String status;
  final double size;

  const StatusBadge({super.key, required this.status, this.size = 8});

  Color _getColor() {
    switch (status.toLowerCase()) {
      case 'running':
      case 'live':
      case 'success':
      case 'active':
      case 'ready':
        return Colors.green;
      case 'building':
      case 'deploying':
      case 'pending':
      case 'creating':
        return Colors.orange;
      case 'failed':
      case 'error':
        return Colors.red;
      case 'stopped':
      case 'draft':
        return Colors.grey;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(color: _getColor(), shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(status[0].toUpperCase() + status.substring(1),
          style: Theme.of(context).textTheme.labelSmall?.copyWith(color: _getColor())),
      ],
    );
  }
}
