import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/rag_providers.dart';
import '../widgets/result_card.dart';

class HomePage extends ConsumerWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queryInput = ref.watch(queryInputProvider);
    final queryResults = ref.watch(queryResultsProvider(queryInput));

    return Scaffold(
      appBar: AppBar(
        title: const Text("ChunkLab App"),
        elevation: 0,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              onChanged: (value) {
                // Update the provider when text changes (you'll need to add logic)
                ref.read(queryInputProvider.notifier).state = value;
              },
              decoration: InputDecoration(
                hintText: 'Ask about Stoicism, virtue, discipline...',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: () {
                    // Trigger search manually if needed
                    // ref.refresh(queryResultsProvider(queryInput));
                  },
                ),
              ),
            ),
          ),
          Expanded(
            child: queryResults.when(
              data: (response) {
                if (response.results.isEmpty) {
                  return const Center(
                    child: Text('No results. Try a different query.'),
                  );
                }
                return ListView.builder(
                  itemCount: response.results.length,
                  itemBuilder: (context, index) {
                    final result = response.results[index];
                    return ResultCard(result: result);
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stack) => Center(
                child: Text('Error: $error'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}