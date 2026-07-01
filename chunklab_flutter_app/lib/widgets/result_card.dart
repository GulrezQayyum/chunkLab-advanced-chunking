import 'package:flutter/material.dart';
import '../models/query_models.dart';

class ResultCard extends StatefulWidget {
  final ChunkResult result;
  final int? index; // optional rank number

  const ResultCard({
    Key? key,
    required this.result,
    this.index, // <-- make sure this line exists
  }) : super(key: key);

  @override
  State<ResultCard> createState() => _ResultCardState();
}

class _ResultCardState extends State<ResultCard> {
  bool _showParent = false;

  @override
  Widget build(BuildContext context) {
    // ✅ use 'similarity' (not 'similarityScore')
    final score = widget.result.similarityScore; // default to 0 if null
    final scoreColor = score > 0.5
        ? Colors.green
        : score > 0.3
        ? Colors.orange
        : Colors.red;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Optional rank
            if (widget.index != null)
              Row(
                children: [
                  Text(
                    '#${widget.index}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey[600],
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
              ),

            // Similarity badge
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: scoreColor.withOpacity(0.15),
                border: Border.all(color: scoreColor.withOpacity(0.5)),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                '${(score * 100).toStringAsFixed(0)}% relevance',
                style: TextStyle(
                  color: scoreColor,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Child chunk text
            Text(
              widget.result.text,
              maxLines: 5,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 14, height: 1.5),
            ),
            const SizedBox(height: 12),

            // View context button (only if parentContext exists)
            if (widget.result.parentContext != null)
              SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: () {
                    setState(() => _showParent = !_showParent);
                  },
                  child: Text(
                    _showParent ? '▼ Hide full context' : '▶ View full context',
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
              ),

            // Parent context (expanded)
            if (_showParent && widget.result.parentContext != null)
              Container(
                margin: const EdgeInsets.only(top: 8),
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.grey[50],
                  border: Border.all(color: Colors.grey[300]!),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'FULL CONTEXT',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: Colors.grey[600],
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      widget.result.parentContext!.text,
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.grey[700],
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
