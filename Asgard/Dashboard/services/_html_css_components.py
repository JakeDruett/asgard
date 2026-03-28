"""
Asgard Dashboard CSS - Component styles.

Table, badge, filter, chart, and error styles extracted from _html_templates.py.
"""

COMPONENT_CSS = """
/* Table */
.table-wrap {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    overflow: hidden;
    margin-bottom: 24px;
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.87rem;
}

thead th {
    background: #2d3748;
    color: #e2e8f0;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

tbody tr:nth-child(even) {
    background: #f7fafc;
}

tbody tr:hover {
    background: #ebf8ff;
}

tbody td {
    padding: 9px 14px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: middle;
}

/* Severity badges */
.sev-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #fff;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.sev-critical { background: #e74c3c; }
.sev-high { background: #e67e22; }
.sev-medium { background: #f39c12; }
.sev-low { background: #3498db; }
.sev-info { background: #95a5a6; }

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

.status-open { background: #fef3cd; color: #856404; }
.status-confirmed { background: #fde8e8; color: #991b1b; }
.status-resolved { background: #d1fae5; color: #065f46; }
.status-closed { background: #e5e7eb; color: #374151; }
.status-false_positive { background: #e0e7ff; color: #3730a3; }
.status-wont_fix { background: #f3f4f6; color: #6b7280; }

/* Filter bar */
.filter-bar {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.filter-bar label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #4a5568;
}

.filter-bar select {
    padding: 6px 12px;
    border: 1px solid #cbd5e0;
    border-radius: 5px;
    font-size: 0.85rem;
    background: #fff;
    color: #2d3748;
    cursor: pointer;
}

.filter-bar button {
    padding: 6px 16px;
    background: #3182ce;
    color: #fff;
    border: none;
    border-radius: 5px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
}

.filter-bar button:hover {
    background: #2b6cb0;
}

/* Pagination info */
.pagination-info {
    font-size: 0.82rem;
    color: #718096;
    margin-bottom: 10px;
}

/* Bar chart */
.bar-chart {
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    padding: 20px 24px;
    margin-bottom: 24px;
}

.bar-chart-title {
    font-size: 0.88rem;
    font-weight: 700;
    color: #4a5568;
    margin-bottom: 14px;
}

.bar-row {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    gap: 10px;
}

.bar-label {
    min-width: 110px;
    font-size: 0.78rem;
    color: #718096;
    text-align: right;
    flex-shrink: 0;
}

.bar-outer {
    flex: 1;
    background: #e2e8f0;
    border-radius: 4px;
    height: 18px;
    overflow: hidden;
}

.bar-inner {
    height: 100%;
    border-radius: 4px;
    background: #3182ce;
    transition: width 0.3s;
}

.bar-value {
    min-width: 36px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #2d3748;
}

/* Timestamp */
.ts {
    font-size: 0.78rem;
    color: #a0aec0;
}

/* Error page */
.error-container {
    max-width: 480px;
    margin: 80px auto;
    background: #fff;
    border-radius: 8px;
    padding: 36px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    text-align: center;
}

.error-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #e74c3c;
    margin-bottom: 14px;
}

.error-message {
    font-size: 0.92rem;
    color: #4a5568;
    line-height: 1.6;
}
"""
