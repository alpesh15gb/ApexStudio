import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class WorkspaceScreen extends ConsumerStatefulWidget {
  final String projectId;

  const WorkspaceScreen({super.key, required this.projectId});

  @override
  ConsumerState<WorkspaceScreen> createState() => _WorkspaceScreenState();
}

class _WorkspaceScreenState extends ConsumerState<WorkspaceScreen> {
  bool _isSidebarOpen = true;
  bool _isBottomPanelOpen = true;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: Icon(_isSidebarOpen ? Icons.menu_open : Icons.menu),
          onPressed: () => setState(() => _isSidebarOpen = !_isSidebarOpen),
        ),
        title: const Text('Workspace'),
        actions: [
          _buildStatusBadge(theme),
          const SizedBox(width: 8),
          IconButton(icon: const Icon(Icons.rocket_launch_outlined), onPressed: () {}, tooltip: 'Deploy'),
          IconButton(icon: const Icon(Icons.settings_outlined), onPressed: () {}, tooltip: 'Settings'),
        ],
      ),
      body: Row(
        children: [
          // Left Sidebar
          if (_isSidebarOpen)
            SizedBox(
              width: 250,
              child: _buildSidebar(theme),
            ),

          // Main content area with right panel
          Expanded(
            child: Column(
              children: [
                // Center — AI Chat area
                Expanded(
                  flex: 3,
                  child: _buildChatArea(theme),
                ),

                // Bottom panel — Terminal / Build Logs / Problems
                if (_isBottomPanelOpen)
                  GestureDetector(
                    onVerticalDragEnd: (details) {
                      if (details.primaryVelocity != null && details.primaryVelocity! > 500) {
                        setState(() => _isBottomPanelOpen = false);
                      }
                    },
                    child: Container(
                      height: 200,
                      decoration: BoxDecoration(
                        border: Border(top: BorderSide(color: theme.dividerColor)),
                      ),
                      child: _buildBottomPanel(theme),
                    ),
                  ),

                // Bottom panel toggle
                if (!_isBottomPanelOpen)
                  GestureDetector(
                    onVerticalDragEnd: (details) {
                      if (details.primaryVelocity != null && details.primaryVelocity! < -500) {
                        setState(() => _isBottomPanelOpen = true);
                      }
                    },
                    child: Container(
                      height: 32,
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        border: Border(top: BorderSide(color: theme.dividerColor)),
                      ),
                      child: Center(child: Icon(Icons.keyboard_arrow_up, size: 20, color: theme.colorScheme.onSurfaceVariant)),
                    ),
                  ),
              ],
            ),
          ),

          // Right — Live Preview
          SizedBox(
            width: 400,
            child: _buildPreview(theme),
          ),
        ],
      ),
    );
  }

  Widget _buildSidebar(ThemeData theme) {
    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        border: Border(right: BorderSide(color: theme.dividerColor)),
      ),
      child: Column(
        children: [
          _SidebarItem(icon: Icons.chat_outlined, label: 'Chat', selected: true),
          _SidebarItem(icon: Icons.folder_outlined, label: 'Files', selected: false),
          _SidebarItem(icon: Icons.storage_outlined, label: 'Database', selected: false),
          _SidebarItem(icon: Icons.code, label: 'API', selected: false),
          _SidebarItem(icon: Icons.cloud_outlined, label: 'Deployments', selected: false),
          const Spacer(),
          _SidebarItem(icon: Icons.checklist, label: 'AI Activity', selected: false),
        ],
      ),
    );
  }

  Widget _buildChatArea(ThemeData theme) {
    return Column(
      children: [
        // Messages
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _ChatBubble(
                isUser: false,
                message: "Hi! I'm your AI development agent. I can help you build your application. What would you like to work on?",
                time: 'Just now',
              ),
              const SizedBox(height: 12),
              _ChatBubble(
                isUser: true,
                message: "Let's build a Payroll and HRMS application for India",
                time: 'Just now',
              ),
            ],
          ),
        ),
        // Input
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest,
            border: Border(top: BorderSide(color: theme.dividerColor)),
          ),
          child: Row(
            children: [
              IconButton(icon: const Icon(Icons.attach_file), onPressed: () {}),
              Expanded(
                child: TextField(
                  decoration: InputDecoration(
                    hintText: 'Ask the AI to build something...',
                    filled: true,
                    fillColor: theme.colorScheme.surface,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(24),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                onPressed: () {},
                icon: const Icon(Icons.send),
                style: IconButton.styleFrom(backgroundColor: theme.colorScheme.primary),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildBottomPanel(ThemeData theme) {
    return DefaultTabController(
      length: 3,
      child: Column(
        children: [
          TabBar(
            tabs: const [
              Tab(text: 'Terminal', icon: Icon(Icons.terminal, size: 16)),
              Tab(text: 'Build Logs', icon: Icon(Icons.build, size: 16)),
              Tab(text: 'Problems', icon: Icon(Icons.warning_amber, size: 16)),
            ],
            labelColor: theme.colorScheme.primary,
            unselectedLabelColor: theme.colorScheme.onSurfaceVariant,
          ),
          Expanded(
            child: TabBarView(
              children: [
                _buildTerminal(theme),
                const Center(child: Text('Build logs will appear here')),
                const Center(child: Text('No problems detected')),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTerminal(ThemeData theme) {
    return Container(
      color: Colors.black87,
      padding: const EdgeInsets.all(8),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('\$', style: TextStyle(color: Color(0xFF4AF626), fontFamily: 'monospace', fontSize: 13)),
          Expanded(child: SizedBox()),
          _TerminalInput(),
        ],
      ),
    );
  }

  Widget _buildPreview(ThemeData theme) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(left: BorderSide(color: theme.dividerColor)),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              border: Border(bottom: BorderSide(color: theme.dividerColor)),
            ),
            child: Row(
              children: [
                Text('Preview', style: theme.textTheme.titleSmall),
                const Spacer(),
                Icon(Icons.refresh, size: 16),
              ],
            ),
          ),
          Expanded(
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.web, size: 64, color: theme.colorScheme.onSurfaceVariant.withOpacity(0.3)),
                  const SizedBox(height: 16),
                  Text('Start a build to see the preview', style: TextStyle(color: theme.colorScheme.onSurfaceVariant)),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.green.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.green.withOpacity(0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 8, height: 8, decoration: const BoxDecoration(color: Colors.green, shape: BoxShape.circle)),
          const SizedBox(width: 6),
          Text('Ready', style: theme.textTheme.labelSmall?.copyWith(color: Colors.green)),
        ],
      ),
    );
  }
}

// --- Sub-widgets ---

class _SidebarItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;

  const _SidebarItem({required this.icon, required this.label, required this.selected});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color = selected ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: selected ? BoxDecoration(
        color: theme.colorScheme.primaryContainer.withOpacity(0.3),
        border: Border(right: BorderSide(color: theme.colorScheme.primary, width: 3)),
      ) : null,
      child: Row(
        children: [
          Icon(icon, size: 20, color: color),
          const SizedBox(width: 12),
          Text(label, style: TextStyle(color: color, fontWeight: selected ? FontWeight.w600 : FontWeight.normal)),
        ],
      ),
    );
  }
}

class _ChatBubble extends StatelessWidget {
  final bool isUser;
  final String message;
  final String time;

  const _ChatBubble({required this.isUser, required this.message, required this.time});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!isUser) ...[
          CircleAvatar(
            radius: 16,
            backgroundColor: theme.colorScheme.primaryContainer,
            child: Icon(Icons.auto_awesome, size: 16, color: theme.colorScheme.onPrimaryContainer),
          ),
          const SizedBox(width: 8),
        ],
        Flexible(
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: isUser ? theme.colorScheme.primary : theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(12),
                topRight: const Radius.circular(12),
                bottomLeft: isUser ? const Radius.circular(12) : Radius.zero,
                bottomRight: isUser ? Radius.zero : const Radius.circular(12),
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(message, style: TextStyle(color: isUser ? theme.colorScheme.onPrimary : null)),
                const SizedBox(height: 4),
                Text(time, style: theme.textTheme.labelSmall?.copyWith(
                  color: isUser ? theme.colorScheme.onPrimary.withOpacity(0.7) : theme.colorScheme.onSurfaceVariant,
                )),
              ],
            ),
          ),
        ),
        if (isUser) const SizedBox(width: 8),
      ],
    );
  }
}

class _TerminalInput extends StatefulWidget {
  const _TerminalInput();

  @override
  State<_TerminalInput> createState() => _TerminalInputState();
}

class _TerminalInputState extends State<_TerminalInput> {
  final _controller = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        const Text('\$ ', style: TextStyle(color: Color(0xFF4AF626), fontFamily: 'monospace', fontSize: 13)),
        Expanded(
          child: TextField(
            controller: _controller,
            style: const TextStyle(color: Color(0xFF4AF626), fontFamily: 'monospace', fontSize: 13),
            decoration: const InputDecoration(border: InputBorder.none, isDense: true),
            onSubmitted: (v) {
              _controller.clear();
            },
          ),
        ),
      ],
    );
  }
}
