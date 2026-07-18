import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/login_screen.dart';
import '../../features/auth/register_screen.dart';
import '../../features/dashboard/dashboard_screen.dart';
import '../../features/projects/project_list_screen.dart';
import '../../features/projects/project_detail_screen.dart';
import '../../features/workspace/workspace_screen.dart';
import '../../features/settings/settings_screen.dart';

final _rootNavigatorKey = GlobalKey<NavigatorState>();

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    navigatorKey: _rootNavigatorKey,
    initialLocation: '/login',
    routes: [
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
      GoRoute(
        path: '/',
        builder: (_, __) => const DashboardScreen(),
        routes: [
          GoRoute(
            path: 'projects',
            builder: (_, __) => const ProjectListScreen(),
            routes: [
              GoRoute(
                path: ':projectId',
                builder: (_, state) => ProjectDetailScreen(
                  projectId: state.pathParameters['projectId']!,
                ),
                routes: [
                  GoRoute(
                    path: 'workspace',
                    builder: (_, state) => WorkspaceScreen(
                      projectId: state.pathParameters['projectId']!,
                    ),
                  ),
                ],
              ),
            ],
          ),
          GoRoute(path: 'settings', builder: (_, __) => const SettingsScreen()),
        ],
      ),
    ],
  );
});
