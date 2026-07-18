import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';

final projectListProvider = FutureProvider.family<List<dynamic>, String>((ref, workspaceId) async {
  final api = ref.read(apiClientProvider);
  final response = await api.getProjects(workspaceId);
  return response.data as List<dynamic>;
});

final projectProvider =
    StateNotifierProvider.family<ProjectNotifier, AsyncValue<Map<String, dynamic>>, String>(
  (ref, projectId) => ProjectNotifier(ref.read(apiClientProvider), projectId),
);

class ProjectNotifier extends StateNotifier<AsyncValue<Map<String, dynamic>>> {
  final ApiClient _api;
  final String _projectId;

  ProjectNotifier(this._api, this._projectId) : super(const AsyncValue.loading()) {
    _load();
  }

  Future<void> _load() async {
    try {
      final response = await _api.get('/projects/$_projectId');
      state = AsyncValue.data(response.data as Map<String, dynamic>);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
    }
  }
}
