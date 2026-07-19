import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class RecentProjects extends StatelessWidget {
  final List<dynamic> projects;

  const RecentProjects({super.key, required this.projects});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (projects.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.folder_open, size: 64, color: theme.colorScheme.onSurfaceVariant.withOpacity(0.5)),
            const SizedBox(height: 16),
            Text('No projects yet', style: theme.textTheme.titleMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 8),
            Text('Create your first project to get started', style: theme.textTheme.bodyMedium?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () => context.go('/projects'),
              icon: const Icon(Icons.add),
              label: const Text('Create Project'),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      itemCount: projects.length > 5 ? 5 : projects.length,
      separatorBuilder: (_, __) => const Divider(height: 1),
      itemBuilder: (_, i) {
        final p = projects[i];
        return ListTile(
          leading: Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: theme.colorScheme.primaryContainer.withOpacity(0.5),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.folder_outlined, color: theme.colorScheme.primary),
          ),
          title: Text(p['name'] ?? 'Untitled', style: const TextStyle(fontWeight: FontWeight.w500)),
          subtitle: Row(
            children: [
              _StatusDot(p['status'] ?? 'draft'),
              const SizedBox(width: 6),
              Text(_statusLabel(p['status'] ?? 'draft'), style: theme.textTheme.bodySmall),
              const SizedBox(width: 12),
              Text(_timeAgo(p['created_at'] ?? ''), style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            ],
          ),
          trailing: const Icon(Icons.chevron_right, size: 20),
          onTap: () => context.go('/projects/${p['id']}'),
        );
      },
    );
  }

  String _statusLabel(String status) {
    return status[0].toUpperCase() + status.substring(1);
  }

  String _timeAgo(String createdAt) {
    if (createdAt.isEmpty) return '';
    // Simple relative time — just show date for now
    try {
      final dt = DateTime.parse(createdAt);
      final diff = DateTime.now().difference(dt);
      if (diff.inMinutes < 1) return 'Just now';
      if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
      if (diff.inHours < 24) return '${diff.inHours}h ago';
      return '${diff.inDays}d ago';
    } catch (_) {
      return '';
    }
  }
}

class _StatusDot extends StatelessWidget {
  final String status;
  const _StatusDot(this.status);

  Color _color() {
    switch (status) {
      case 'ready': case 'deployed': case 'running': return Colors.green;
      case 'building': case 'deploying': case 'discovering': case 'planning': return Colors.orange;
      case 'failed': return Colors.red;
      default: return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(width: 8, height: 8, decoration: BoxDecoration(color: _color(), shape: BoxShape.circle));
  }
}
