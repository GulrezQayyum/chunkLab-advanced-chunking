import 'package:chunklab_flutter_app/widgets/result_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:chunklab_flutter_app/providers/rag_providers.dart';

class HomePage extends ConsumerStatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  late TextEditingController _queryController; // ✅ underscore
  String _lastQuery = '';

  @override
  void initState() {
    super.initState();
    _queryController = TextEditingController(); // ✅ underscore
  }

  @override
  void dispose() {
    _queryController.dispose(); // ✅ underscore
    super.dispose();
  }

  void _performSearch() { // ✅ underscore (private method)
    final query = _queryController.text.trim(); // ✅ underscore
    if (query.isNotEmpty) { // ✅ .isNotEmpty (getter, not method)
      setState(() => _lastQuery = query);
      final strategy = ref.read(selectedStrategyProvider); // ✅ correct syntax
      print('🔍 Searching: "$query" using ${strategy.label} strategy');

      // ✅ correct use of unawaited (import dart:async)
      (
        ref.refresh(queryResultsProvider((query: query, strategy: strategy))),
      );
    } // closes if
  } // closes method

  void _clearSearch() {
    _queryController.clear(); // ✅ underscore
    setState(() => _lastQuery = '');
  }

  @override
  Widget build(BuildContext context) {
    final selectedStrategy = ref.watch(selectedStrategyProvider); // ✅ correct


    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('🧠 ChunkLab RAG'),
            Text(
              'Strategy: ${selectedStrategy.label}',
              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.normal),
            ),
          ],
        ),
        elevation: 2,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              elevation: 1,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Chunking Strategy',
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
                    const SizedBox(height: 8),
                    Consumer(
                      builder: (context, ref, child) {
                        return DropdownButton<ChunkingStrategy>(
                          value: selectedStrategy,
                          isExpanded: true,
                          items: ChunkingStrategy.values
                              .map((strategy) => DropdownMenuItem(
                                    value: strategy,
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      mainAxisAlignment: MainAxisAlignment.center,
                                      children: [
                                        Text(
                                          strategy.label,
                                          style: const TextStyle(fontWeight: FontWeight.w500),
                                        ),
                                        Text(
                                          strategy.description,
                                          style: Theme.of(context).textTheme.bodySmall,
                                        ),
                                      ],
                                    ),
                                  ))
                              .toList(),
                          onChanged: (strategy) {
                            if (strategy != null) {
                              ref.read(selectedStrategyProvider.notifier).state = strategy;
                              if (_lastQuery.isNotEmpty) {
                                Future.delayed(const Duration(milliseconds: 300), _performSearch);
                              }
                            }
                          },
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            TextField(
              controller: _queryController,
              decoration: InputDecoration(
                hintText: 'Enter your query (e.g., "virtue reason")',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _queryController.text.isNotEmpty
                    ? IconButton(icon: const Icon(Icons.clear), onPressed: _clearSearch)
                    : null,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                filled: true,
                fillColor: Colors.grey[50],
              ),
              onChanged: (_) => setState(() {}),
              onSubmitted: (_) => _performSearch(),
            ),
            const SizedBox(height: 8),

            ElevatedButton.icon(
              onPressed: _performSearch,
              icon: const Icon(Icons.search),
              label: const Text('Search'),
              style: ElevatedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 12)),
            ),
            const SizedBox(height: 24),

            if (_lastQuery.isNotEmpty) ...[
              Text(
                'Results for "$_lastQuery"',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              Consumer(
                builder: (context, ref, child) {
                  final queryAsync = ref.watch(
                    queryResultsProvider((query: _lastQuery, strategy: selectedStrategy)),
                  );
                  return queryAsync.when(
                    data: (response) {
                      if (response.results.isEmpty) {
                        return Center(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(vertical: 24),
                            child: Column(
                              children: [
                                const Icon(Icons.search_off, size: 48, color: Colors.grey),
                                const SizedBox(height: 12),
                                Text('No results found', style: Theme.of(context).textTheme.bodyLarge),
                                const SizedBox(height: 4),
                                Text('Try a different query', style: Theme.of(context).textTheme.bodySmall),
                              ],
                            ),
                          ),
                        );
                      }
                      return Column(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: Colors.blue[50],
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: Colors.blue[200]!),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'Results: ${response.totalResults}',
                                  style: const TextStyle(fontWeight: FontWeight.w600),
                                ),
                                Text(
                                  'Avg Similarity: ${(response.metrics?['avg_similarity'] ?? 0).toStringAsFixed(3)}',
                                  style: const TextStyle(fontWeight: FontWeight.w600),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 12),
                          ...response.results.asMap().entries.map((entry) {
                            final index = entry.key;
                            final result = entry.value;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: ResultCard(result: result, index: index + 1),
                            );
                          }),
                        ],
                      );
                    },
                    loading: () => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 24),
                      child: Column(
                        children: [
                          const CircularProgressIndicator(),
                          const SizedBox(height: 12),
                          Text(
                            'Searching with ${selectedStrategy.label}...',
                            style: Theme.of(context).textTheme.bodyLarge,
                          ),
                        ],
                      ),
                    ),
                    error: (error, stackTrace) => Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.red[50],
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.red[200]!),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Error',
                            style: Theme.of(context).textTheme.labelLarge?.copyWith(color: Colors.red[700]),
                          ),
                          const SizedBox(height: 4),
                          Text(error.toString(), style: Theme.of(context).textTheme.bodyMedium),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ] else
              Center(
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 48),
                  child: Column(
                    children: [
                      Icon(Icons.search_off, size: 48, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text(
                        'Try a query',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(color: Colors.grey[600]),
                      ),
                      const SizedBox(height: 8),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        child: Text(
                          'Examples: "virtue reason", "discipline self-control", "nature universe"',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey[500]),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}