import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class RecentProjects extends ConsumerWidget {
  const RecentProjects({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    // Placeholder — will be wired to project list API
    final projects = <Map<String, String>>[];

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

    return ListView.builder(
      itemCount: projects.length,
      itemBuilder: (_, i) => ListTile(
        leading: const Icon(Icons.folder_outlined),
        title: Text(projects[i]['name'] ?? ''),
        subtitle: Text(projects[i]['status'] ?? ''),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.go('/projects/${projects[i]['id']}'),
      ),
    );
  }
}
