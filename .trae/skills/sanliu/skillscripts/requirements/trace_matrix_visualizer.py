#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
追溯矩阵可视化器
生成可视化的追溯矩阵图表
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum


@dataclass
class VisualizationNode:
    id: str
    label: str
    node_type: str
    status: str
    x: float = 0.0
    y: float = 0.0
    size: int = 30
    color: str = "#409EFF"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type,
            "status": self.status,
            "x": self.x,
            "y": self.y,
            "size": self.size,
            "color": self.color
        }


@dataclass
class VisualizationEdge:
    id: str
    source: str
    target: str
    edge_type: str
    status: str
    color: str = "#909399"
    width: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.edge_type,
            "status": self.status,
            "color": self.color,
            "width": self.width
        }


@dataclass
class VisualizationGraph:
    nodes: List[VisualizationNode]
    edges: List[VisualizationEdge]
    layout: str = "hierarchical"
    title: str = "需求追溯矩阵"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "layout": self.layout,
            "title": self.title,
            "generated_at": self.generated_at
        }


@dataclass
class CoverageHeatmap:
    categories: List[str]
    values: List[float]
    labels: List[str]
    colors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "categories": self.categories,
            "values": self.values,
            "labels": self.labels,
            "colors": self.colors
        }


@dataclass
class TraceVisualization:
    graph: VisualizationGraph
    heatmap: CoverageHeatmap
    statistics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph": self.graph.to_dict(),
            "heatmap": self.heatmap.to_dict(),
            "statistics": self.statistics
        }


class TraceMatrixVisualizer:
    TYPE_COLORS = {
        "requirement": "#409EFF",
        "user_story": "#67C23A",
        "feature": "#E6A23C",
        "test_case": "#F56C6C",
        "acceptance_test": "#909399"
    }
    
    STATUS_COLORS = {
        "covered": "#67C23A",
        "verified": "#67C23A",
        "pending": "#E6A23C",
        "failed": "#F56C6C",
        "partial": "#E6A23C",
        "uncovered": "#F56C6C",
        "active": "#409EFF",
        "passed": "#67C23A"
    }
    
    EDGE_COLORS = {
        "requirement_to_test": "#409EFF",
        "requirement_to_feature": "#67C23A",
        "feature_to_test": "#E6A23C",
        "user_story_to_test": "#909399"
    }
    
    def __init__(self):
        self.node_counter = 0
        self.edge_counter = 0
    
    def _generate_node_id(self) -> str:
        self.node_counter += 1
        return f"node_{self.node_counter}"
    
    def _generate_edge_id(self) -> str:
        self.edge_counter += 1
        return f"edge_{self.edge_counter}"
    
    def _get_node_color(self, node_type: str, status: str) -> str:
        if status in self.STATUS_COLORS:
            return self.STATUS_COLORS[status]
        return self.TYPE_COLORS.get(node_type, "#909399")
    
    def _calculate_hierarchical_layout(self, 
                                        nodes: List[VisualizationNode],
                                        edges: List[VisualizationEdge]) -> List[VisualizationNode]:
        levels: Dict[str, int] = {}
        
        type_order = {
            "requirement": 0,
            "user_story": 1,
            "feature": 1,
            "test_case": 2,
            "acceptance_test": 2
        }
        
        for node in nodes:
            levels[node.id] = type_order.get(node.node_type, 0)
        
        for edge in edges:
            source_level = levels.get(edge.source, 0)
            target_level = levels.get(edge.target, 0)
            if target_level <= source_level:
                levels[edge.target] = source_level + 1
        
        level_nodes: Dict[int, List[VisualizationNode]] = {}
        for node in nodes:
            level = levels.get(node.id, 0)
            if level not in level_nodes:
                level_nodes[level] = []
            level_nodes[level].append(node)
        
        max_level = max(level_nodes.keys()) if level_nodes else 0
        
        for level, nodes_at_level in level_nodes.items():
            count = len(nodes_at_level)
            y = level * 150 + 50
            for i, node in enumerate(nodes_at_level):
                node.x = (i + 1) * (800 / (count + 1))
                node.y = y
        
        return nodes
    
    def create_graph_from_matrix(self, matrix_data: Dict[str, Any]) -> VisualizationGraph:
        nodes: List[VisualizationNode] = []
        edges: List[VisualizationEdge] = []
        
        node_id_map: Dict[str, str] = {}
        
        for req in matrix_data.get("requirements", []):
            node_id = self._generate_node_id()
            node_id_map[req["id"]] = node_id
            
            node = VisualizationNode(
                id=node_id,
                label=req["name"],
                node_type="requirement",
                status=req.get("status", "active"),
                color=self._get_node_color("requirement", req.get("status", "active"))
            )
            nodes.append(node)
        
        for test in matrix_data.get("test_cases", []):
            node_id = self._generate_node_id()
            node_id_map[test["id"]] = node_id
            
            status = test.get("execution_result") or test.get("status", "pending")
            node = VisualizationNode(
                id=node_id,
                label=test["name"],
                node_type="test_case",
                status=status,
                color=self._get_node_color("test_case", status)
            )
            nodes.append(node)
        
        for link in matrix_data.get("trace_links", []):
            source_id = node_id_map.get(link["source_id"])
            target_id = node_id_map.get(link["target_id"])
            
            if source_id and target_id:
                edge = VisualizationEdge(
                    id=self._generate_edge_id(),
                    source=source_id,
                    target=target_id,
                    edge_type=link.get("trace_type", "requirement_to_test"),
                    status=link.get("status", "pending"),
                    color=self.EDGE_COLORS.get(link.get("trace_type"), "#909399")
                )
                edges.append(edge)
        
        nodes = self._calculate_hierarchical_layout(nodes, edges)
        
        return VisualizationGraph(
            nodes=nodes,
            edges=edges,
            title="需求追溯矩阵"
        )
    
    def create_coverage_heatmap(self, coverage_data: Dict[str, Any]) -> CoverageHeatmap:
        categories = []
        values = []
        labels = []
        colors = []
        
        total = coverage_data.get("total_requirements", 0)
        covered = coverage_data.get("covered_requirements", 0)
        verified = coverage_data.get("verified_requirements", 0)
        uncovered = total - covered
        
        categories = ["已覆盖", "已验证", "未覆盖"]
        values = [covered, verified, uncovered]
        labels = [f"{v} ({v/total*100:.1f}%)" if total > 0 else "0 (0%)" for v in values]
        colors = ["#67C23A", "#409EFF", "#F56C6C"]
        
        return CoverageHeatmap(
            categories=categories,
            values=values,
            labels=labels,
            colors=colors
        )
    
    def generate_visualization(self, matrix_data: Dict[str, Any]) -> TraceVisualization:
        graph = self.create_graph_from_matrix(matrix_data)
        heatmap = self.create_coverage_heatmap(matrix_data.get("coverage_stats", {}))
        
        statistics = {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "node_types": {},
            "edge_types": {}
        }
        
        for node in graph.nodes:
            node_type = node.node_type
            statistics["node_types"][node_type] = statistics["node_types"].get(node_type, 0) + 1
        
        for edge in graph.edges:
            edge_type = edge.edge_type
            statistics["edge_types"][edge_type] = statistics["edge_types"].get(edge_type, 0) + 1
        
        return TraceVisualization(
            graph=graph,
            heatmap=heatmap,
            statistics=statistics
        )
    
    def to_html(self, visualization: TraceVisualization) -> str:
        html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>需求追溯矩阵可视化</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #409EFF, #67C23A);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        .header p {
            opacity: 0.9;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #409EFF;
        }
        .stat-label {
            color: #909399;
            margin-top: 5px;
        }
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }
        .chart-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            color: #303133;
            border-left: 4px solid #409EFF;
            padding-left: 10px;
        }
        #graph-chart {
            width: 100%;
            height: 600px;
        }
        #heatmap-chart {
            width: 100%;
            height: 400px;
        }
        .legend {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        .footer {
            text-align: center;
            color: #909399;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>需求追溯矩阵可视化</h1>
            <p>生成时间: ''' + visualization.graph.generated_at + '''</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">''' + str(visualization.statistics.get("total_nodes", 0)) + '''</div>
                <div class="stat-label">总节点数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(visualization.statistics.get("total_edges", 0)) + '''</div>
                <div class="stat-label">追溯链接</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(visualization.statistics.get("node_types", {}).get("requirement", 0)) + '''</div>
                <div class="stat-label">需求数量</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(visualization.statistics.get("node_types", {}).get("test_case", 0)) + '''</div>
                <div class="stat-label">测试用例</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">追溯关系图</div>
            <div id="graph-chart"></div>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #409EFF;"></div>
                    <span>需求</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #F56C6C;"></div>
                    <span>测试用例</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #67C23A;"></div>
                    <span>已覆盖</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #E6A23C;"></div>
                    <span>待处理</span>
                </div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">覆盖率热力图</div>
            <div id="heatmap-chart"></div>
        </div>
        
        <div class="footer">
            <p>需求追溯矩阵可视化工具 | 自动生成</p>
        </div>
    </div>
    
    <script>
        // 图数据
        const graphData = ''' + json.dumps(visualization.graph.to_dict(), ensure_ascii=False) + ''';
        
        // 热力图数据
        const heatmapData = ''' + json.dumps(visualization.heatmap.to_dict(), ensure_ascii=False) + ''';
        
        // 渲染追溯关系图
        const graphChart = echarts.init(document.getElementById('graph-chart'));
        const graphOption = {
            tooltip: {
                trigger: 'item',
                formatter: function(params) {
                    if (params.dataType === 'node') {
                        return params.data.label + '<br/>类型: ' + params.data.type + '<br/>状态: ' + params.data.status;
                    } else {
                        return '追溯链接';
                    }
                }
            },
            series: [{
                type: 'graph',
                layout: 'none',
                symbolSize: 40,
                roam: true,
                label: {
                    show: true,
                    position: 'bottom',
                    fontSize: 12
                },
                edgeSymbol: ['none', 'arrow'],
                edgeSymbolSize: [4, 10],
                data: graphData.nodes.map(node => ({
                    id: node.id,
                    name: node.label,
                    label: node.label,
                    type: node.type,
                    status: node.status,
                    x: node.x,
                    y: node.y,
                    itemStyle: {
                        color: node.color
                    }
                })),
                links: graphData.edges.map(edge => ({
                    source: edge.source,
                    target: edge.target,
                    lineStyle: {
                        color: edge.color,
                        width: edge.width
                    }
                })),
                lineStyle: {
                    opacity: 0.9,
                    width: 2,
                    curveness: 0
                }
            }]
        };
        graphChart.setOption(graphOption);
        
        // 渲染热力图
        const heatmapChart = echarts.init(document.getElementById('heatmap-chart'));
        const heatmapOption = {
            tooltip: {
                trigger: 'item',
                formatter: '{b}: {c}'
            },
            xAxis: {
                type: 'category',
                data: heatmapData.categories,
                axisLabel: {
                    fontSize: 14
                }
            },
            yAxis: {
                type: 'value',
                name: '数量'
            },
            series: [{
                type: 'bar',
                data: heatmapData.categories.map((cat, i) => ({
                    value: heatmapData.values[i],
                    itemStyle: {
                        color: heatmapData.colors[i]
                    }
                })),
                label: {
                    show: true,
                    position: 'top',
                    formatter: function(params) {
                        return heatmapData.labels[params.dataIndex];
                    }
                },
                barWidth: '50%'
            }]
        };
        heatmapChart.setOption(heatmapOption);
        
        // 响应式调整
        window.addEventListener('resize', function() {
            graphChart.resize();
            heatmapChart.resize();
        });
    </script>
</body>
</html>'''
        
        return html_template
    
    def save_html(self, visualization: TraceVisualization, output_path: str) -> str:
        html_content = self.to_html(visualization)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path


def main():
    visualizer = TraceMatrixVisualizer()
    
    test_matrix_data = {
        "requirements": [
            {"id": "REQ-001", "name": "用户登录功能", "status": "active", "requirement_type": "functional"},
            {"id": "REQ-002", "name": "密码重置功能", "status": "active", "requirement_type": "functional"},
            {"id": "REQ-003", "name": "用户注册功能", "status": "active", "requirement_type": "functional"}
        ],
        "test_cases": [
            {"id": "TC-001", "name": "登录成功测试", "status": "passed", "execution_result": "passed"},
            {"id": "TC-002", "name": "登录失败测试", "status": "passed", "execution_result": "passed"},
            {"id": "TC-003", "name": "密码重置测试", "status": "pending", "execution_result": None}
        ],
        "trace_links": [
            {"source_id": "REQ-001", "target_id": "TC-001", "trace_type": "requirement_to_test", "status": "covered"},
            {"source_id": "REQ-001", "target_id": "TC-002", "trace_type": "requirement_to_test", "status": "covered"},
            {"source_id": "REQ-002", "target_id": "TC-003", "trace_type": "requirement_to_test", "status": "pending"}
        ],
        "coverage_stats": {
            "total_requirements": 3,
            "covered_requirements": 2,
            "verified_requirements": 1,
            "coverage_rate": 66.67
        }
    }
    
    print("="*60)
    print("追溯矩阵可视化测试")
    print("="*60)
    
    visualization = visualizer.generate_visualization(test_matrix_data)
    
    print(f"\n生成可视化数据:")
    print(f"  节点数: {visualization.statistics['total_nodes']}")
    print(f"  边数: {visualization.statistics['total_edges']}")
    print(f"  节点类型: {visualization.statistics['node_types']}")
    
    print("\nJSON输出 (部分):")
    print(json.dumps(visualization.to_dict(), ensure_ascii=False, indent=2)[:1000] + "...")
    
    html_output = visualizer.to_html(visualization)
    print(f"\n生成HTML文档长度: {len(html_output)} 字符")


if __name__ == "__main__":
    main()
