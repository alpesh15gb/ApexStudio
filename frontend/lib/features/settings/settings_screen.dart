import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Profile section
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  CircleAvatar(radius: 30, child: const Icon(Icons.person, size: 30)),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('User Name', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      Text('user@example.com', style: theme.textTheme.bodySmall),
                    ],
                  ),
                  const Spacer(),
                  IconButton(icon: const Icon(Icons.edit_outlined), onPressed: () {}),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Theme
          Card(
            child: Column(
              children: [
                SwitchListTile(
                  title: const Text('Dark Mode'),
                  subtitle: const Text('Use dark theme'),
                  value: Theme.of(context).brightness == Brightness.dark,
                  onChanged: (_) {},
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.palette_outlined),
                  title: const Text('Theme Color'),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(width: 24, height: 24, decoration: const BoxDecoration(color: Colors.purple, shape: BoxShape.circle)),
                      const SizedBox(width: 8),
                      const Icon(Icons.chevron_right),
                    ],
                  ),
                  onTap: () {},
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Account
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.people_outlined),
                  title: const Text('Organization'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.credit_card_outlined),
                  title: const Text('Billing & Plan'),
                  subtitle: const Text('Free Plan'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {},
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // About
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.info_outlined),
                  title: const Text('About Apex Studio'),
                  subtitle: const Text('Version 0.1.0'),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),
          Center(
            child: TextButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.logout, color: Colors.red),
              label: const Text('Sign Out', style: TextStyle(color: Colors.red)),
            ),
          ),
        ],
      ),
    );
  }
}
