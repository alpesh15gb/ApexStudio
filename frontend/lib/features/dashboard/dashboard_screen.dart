import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/api_client.dart';
import '../../core/providers/auth_provider.dart';
import 'widgets/stat_card.dart';
import 'widgets/recent_projects.dart';

final dashboardDataProvider = FutureProvider<DashboardData>((ref) async {
  final api = ref.read(apiClientProvider);
  final orgs = await api.get('/organizations');
  final orgsData = orgs.data as List;

  int totalProjects = 0;
  int totalBuilds = 0;
  int totalDeployments = 0;
  List<dynamic> recentProjects = [];

  if (orgsData.isNotEmpty) {
    final orgId = orgsData[0]['id'];
    final workspaces = await api.get('/workspaces', params: {'organization_id': orgId});
    final wsData = workspaces.data as List;

    if (wsData.isNotEmpty) {
      final wsId = wsData[0]['id'];
      final projects = await api.get('/projects', params: {'workspace_id': wsId});
      final projectsData = projects.data as List;
      totalProjects = projectsData.length;
      recentProjects = projectsData;
    }
  }

  return DashboardData(
    activeProjects: totalProjects,
    runningBuilds: totalBuilds,
    deployments: totalDeployments,
    recentProjects: recentProjects,
  );
});

class DashboardData {
  final int activeProjects;
  final int runningBuilds;
  final int deployments;
  final List<dynamic> recentProjects;

  DashboardData({
    required this.activeProjects,
    required this.runningBuilds,
    required this.deployments,
    required this.recentProjects,
  });
}

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final dashboardAsync = ref.watch(dashboardDataProvider);
    final authState = ref.watch(authProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Apex Studio'),
        actions: [
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            onPressed: () => context.go('/settings'),
          ),
          PopupMenuButton(
            itemBuilder: (_) => [
              const PopupMenuItem(value: 'profile', child: Text('Profile')),
              const PopupMenuItem(value: 'logout', child: Text('Logout')),
            ],
            onSelected: (v) {
              if (v == 'logout') {
                ref.read(authProvider.notifier).logout();
                context.go('/login');
              }
            },
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Welcome back${authState.email != null ? ', ${authState.email!.split('@')[0]}' : ''}!',
              style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text('What would you like to build today?',
              style: theme.textTheme.bodyLarge?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
            const SizedBox(height: 24),
            dashboardAsync.when(
              data: (data) => Row(
                children: [
                  Expanded(child: StatCard(title: 'Active Projects', value: '${data.activeProjects}', icon: Icons.folder_outlined)),
                  const SizedBox(width: 16),
                  Expanded(child: StatCard(title: 'Running Builds', value: '${data.runningBuilds}', icon: Icons.build_outlined)),
                  const SizedBox(width: 16),
                  Expanded(child: StatCard(title: 'Deployments', value: '${data.deployments}', icon: Icons.cloud_outlined)),
                ],
              ),
              loading: () => Row(
                children: List.generate(3, (_) => Expanded(
                  child: Card(child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Container(width: 28, height: 28, decoration: BoxDecoration(color: theme.colorScheme.primary.withOpacity(0.3), borderRadius: BorderRadius.circular(8))),
                      const SizedBox(height: 12),
                      Container(width: 40, height: 28, decoration: BoxDecoration(color: theme.colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(4))),
                      const SizedBox(height: 4),
                      Container(width: 80, height: 16, decoration: BoxDecoration(color: theme.colorScheme.surfaceContainerHighest, borderRadius: BorderRadius.circular(4))),
                    ]),
                  )),
                )).expand((w) => [w, const SizedBox(width: 16)]).toList()..removeLast(),
              ),
              error: (e, _) => Row(
                children: [
                  Expanded(child: StatCard(title: 'Active Projects', value: '0', icon: Icons.folder_outlined)),
                  const SizedBox(width: 16),
                  Expanded(child: StatCard(title: 'Running Builds', value: '0', icon: Icons.build_outlined)),
                  const SizedBox(width: 16),
                  Expanded(child: StatCard(title: 'Deployments', value: '0', icon: Icons.cloud_outlined)),
                ],
              ),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () => context.go('/projects'),
                    icon: const Icon(Icons.add),
                    label: const Text('New Project'),
                    style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.rocket_launch_outlined),
                    label: const Text('Quick Start Guide'),
                    style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 32),
            Text('Recent Projects', style: theme.textTheme.titleLarge),
            const SizedBox(height: 16),
            Expanded(
              child: dashboardAsync.when(
                data: (data) => RecentProjects(projects: data.recentProjects),
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (_, __) => const Center(child: Text('Could not load projects')),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
