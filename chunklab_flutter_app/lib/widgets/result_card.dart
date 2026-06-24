import 'package:flutter/material.dart';
import '../models/chunk_result.dart';

class ResultCard extends StatefulWidget {
  final ChunkResult result;

  const ResultCard({Key? key, required this.result}) : super(key: key);

  @override
  State<ResultCard> createState() => _ResultCardState();
}

class _ResultCardState extends State<ResultCard> {
  bool showParent = false;

  @override
  Widget build(BuildContext context) {
    final score = widget.result.similarityScore;
    final scoreColor = score > 0.5
        ? Colors.green
        : score > 0.3
            ? Colors.orange
            : Colors.red;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Similarity score
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: scoreColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    '${(score * 100).toStringAsFixed(0)}% match',
                    style: TextStyle(
                      color: scoreColor,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            // Child chunk text
            Text(
              widget.result.text,
              maxLines: 4,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 8),
            // Show parent button
            if (widget.result.parentContext != null)
              TextButton(
                onPressed: () {
                  setState(() => showParent = !showParent);
                },
                child: Text(showParent ? 'Hide context' : 'View full context'),
              ),
            // Parent context (if expanded)
            if (showParent && widget.result.parentContext != null)
              Container(
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  widget.result.parentContext!.text,
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ),
          ],
        ),
      ),
    );
  }
}