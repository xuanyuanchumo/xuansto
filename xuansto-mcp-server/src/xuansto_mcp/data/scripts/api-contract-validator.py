#!/usr/bin/env python3
"""
API契约验证脚本
功能：验证实现是否符合OpenAPI规范
"""

import argparse
import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='API契约验证脚本 - 验证实现是否符合OpenAPI规范'
    )
    parser.add_argument(
        '--spec',
        type=str,
        default='openapi.yaml',
        help='OpenAPI规范文件路径（默认：openapi.yaml）'
    )
    parser.add_argument(
        '--base-url',
        type=str,
        default='http://localhost:8000',
        help='API基础URL（默认：http://localhost:8000）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='contract-report',
        help='输出目录名称（默认：contract-report）'
    )
    parser.add_argument(
        '--validate-response',
        action='store_true',
        help='验证实际响应是否符合规范'
    )
    parser.add_argument(
        '--check-deprecated',
        action='store_true',
        help='检查是否使用了已弃用的端点'
    )
    return parser.parse_args()


class OpenAPIParser:
    """OpenAPI规范解析器"""
    
    def __init__(self, spec_path: str):
        """
        初始化解析器
        
        参数:
            spec_path: OpenAPI规范文件路径
        """
        self.spec_path = Path(spec_path)
        self.spec = None
        self.endpoints = []
    
    def load(self) -> bool:
        """
        加载OpenAPI规范
        
        返回:
            是否成功加载
        """
        if not self.spec_path.exists():
            print(f"规范文件不存在: {self.spec_path}")
            return False
        
        try:
            content = self.spec_path.read_text(encoding='utf-8')
            
            if self.spec_path.suffix in ['.yaml', '.yml']:
                try:
                    import yaml
                    self.spec = yaml.safe_load(content)
                except ImportError:
                    print("需要安装PyYAML: pip install pyyaml")
                    return False
            else:
                self.spec = json.loads(content)
            
            self._parse_endpoints()
            return True
            
        except Exception as e:
            print(f"解析规范文件失败: {e}")
            return False
    
    def _parse_endpoints(self):
        """解析所有端点"""
        self.endpoints = []
        
        paths = self.spec.get('paths', {})
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'operation_id': details.get('operationId', ''),
                        'summary': details.get('summary', ''),
                        'deprecated': details.get('deprecated', False),
                        'parameters': details.get('parameters', []),
                        'request_body': details.get('requestBody'),
                        'responses': details.get('responses', {}),
                        'tags': details.get('tags', [])
                    }
                    self.endpoints.append(endpoint)
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        获取所有端点
        
        返回:
            端点列表
        """
        return self.endpoints
    
    def get_endpoint(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """
        获取指定端点
        
        参数:
            path: 端点路径
            method: HTTP方法
        
        返回:
            端点详情或None
        """
        for endpoint in self.endpoints:
            if endpoint['path'] == path and endpoint['method'] == method.upper():
                return endpoint
        return None


class ContractValidator:
    """契约验证器"""
    
    def __init__(self, parser: OpenAPIParser, base_url: str):
        """
        初始化验证器
        
        参数:
            parser: OpenAPI解析器
            base_url: API基础URL
        """
        self.parser = parser
        self.base_url = base_url.rstrip('/')
        self.errors = []
        self.warnings = []
        self.results = []
    
    def validate_spec_structure(self) -> Dict[str, Any]:
        """
        验证规范结构
        
        返回:
            验证结果
        """
        result = {
            'check': 'spec_structure',
            'valid': True,
            'issues': []
        }
        
        spec = self.parser.spec
        
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in spec:
                result['valid'] = False
                result['issues'].append(f"缺少必需字段: {field}")
        
        info = spec.get('info', {})
        info_required = ['title', 'version']
        for field in info_required:
            if field not in info:
                result['valid'] = False
                result['issues'].append(f"info缺少必需字段: {field}")
        
        openapi_version = spec.get('openapi', '')
        if not openapi_version.startswith('3.'):
            result['issues'].append(f"建议使用OpenAPI 3.x版本，当前: {openapi_version}")
        
        self.results.append(result)
        return result
    
    def validate_endpoints(self) -> List[Dict[str, Any]]:
        """
        验证所有端点
        
        返回:
            验证结果列表
        """
        endpoint_results = []
        
        for endpoint in self.parser.get_endpoints():
            result = self._validate_single_endpoint(endpoint)
            endpoint_results.append(result)
            self.results.append(result)
        
        return endpoint_results
    
    def _validate_single_endpoint(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证单个端点
        
        参数:
            endpoint: 端点信息
        
        返回:
            验证结果
        """
        result = {
            'check': 'endpoint',
            'path': endpoint['path'],
            'method': endpoint['method'],
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        if not endpoint['operation_id']:
            result['warnings'].append("缺少operationId")
        
        responses = endpoint.get('responses', {})
        if not responses:
            result['valid'] = False
            result['issues'].append("缺少响应定义")
        else:
            if '200' not in responses and '201' not in responses and '2XX' not in responses:
                result['warnings'].append("缺少成功响应定义(200/201)")
            
            for status_code, response in responses.items():
                if 'description' not in response:
                    result['issues'].append(f"响应 {status_code} 缺少description")
        
        parameters = endpoint.get('parameters', [])
        for param in parameters:
            if 'name' not in param:
                result['issues'].append("参数缺少name字段")
            if 'in' not in param:
                result['issues'].append(f"参数 {param.get('name', 'unknown')} 缺少in字段")
        
        if endpoint.get('deprecated'):
            result['warnings'].append("此端点已标记为deprecated")
        
        if result['issues']:
            result['valid'] = False
        
        return result
    
    def validate_response_schema(self, path: str, method: str, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证响应数据是否符合规范
        
        参数:
            path: 端点路径
            method: HTTP方法
            response_data: 实际响应数据
        
        返回:
            验证结果
        """
        result = {
            'check': 'response_schema',
            'path': path,
            'method': method,
            'valid': True,
            'issues': []
        }
        
        endpoint = self.parser.get_endpoint(path, method)
        if not endpoint:
            result['valid'] = False
            result['issues'].append(f"端点未在规范中定义: {method} {path}")
            return result
        
        responses = endpoint.get('responses', {})
        status_code = str(response_data.get('status_code', 200))
        
        if status_code not in responses:
            result['warnings'] = [f"状态码 {status_code} 未在规范中定义"]
            return result
        
        response_spec = responses[status_code]
        content = response_spec.get('content', {})
        
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            body = response_data.get('body', {})
            
            schema_result = self._validate_against_schema(body, schema)
            if not schema_result['valid']:
                result['valid'] = False
                result['issues'].extend(schema_result['issues'])
        
        return result
    
    def _validate_against_schema(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证数据是否符合Schema
        
        参数:
            data: 实际数据
            schema: JSON Schema
        
        返回:
            验证结果
        """
        result = {
            'valid': True,
            'issues': []
        }
        
        schema_type = schema.get('type')
        
        if schema_type:
            type_mapping = {
                'string': str,
                'number': (int, float),
                'integer': int,
                'boolean': bool,
                'array': list,
                'object': dict
            }
            
            expected_type = type_mapping.get(schema_type)
            if expected_type and not isinstance(data, expected_type):
                result['valid'] = False
                result['issues'].append(f"类型不匹配: 期望 {schema_type}, 实际 {type(data).__name__}")
        
        if schema_type == 'object' or 'properties' in schema:
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            if not isinstance(data, dict):
                result['valid'] = False
                result['issues'].append("期望对象类型")
                return result
            
            for req_field in required:
                if req_field not in data:
                    result['valid'] = False
                    result['issues'].append(f"缺少必需字段: {req_field}")
        
        if schema_type == 'array' or 'items' in schema:
            items_schema = schema.get('items', {})
            if isinstance(data, list):
                for i, item in enumerate(data):
                    item_result = self._validate_against_schema(item, items_schema)
                    if not item_result['valid']:
                        result['valid'] = False
                        result['issues'].append(f"数组项 {i}: {item_result['issues']}")
        
        return result
    
    def check_deprecated_usage(self, used_endpoints: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        检查已弃用端点的使用
        
        参数:
            used_endpoints: 使用的端点列表
        
        返回:
            检查结果
        """
        result = {
            'check': 'deprecated_usage',
            'valid': True,
            'deprecated_found': [],
            'issues': []
        }
        
        deprecated_endpoints = [
            ep for ep in self.parser.get_endpoints() if ep.get('deprecated')
        ]
        
        for used in used_endpoints:
            for dep in deprecated_endpoints:
                if used['path'] == dep['path'] and used['method'] == dep['method']:
                    result['deprecated_found'].append({
                        'path': dep['path'],
                        'method': dep['method'],
                        'summary': dep.get('summary', '')
                    })
        
        if result['deprecated_found']:
            result['issues'] = [f"使用了已弃用端点: {d['method']} {d['path']}" for d in result['deprecated_found']]
        
        return result


def generate_report(output_dir: str, results: Dict[str, Any]):
    """
    生成验证报告
    
    参数:
        output_dir: 输出目录
        results: 验证结果
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    json_file = output_path / f'contract-validation-{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {json_file}")


def print_summary(results: Dict[str, Any]):
    """打印验证摘要"""
    print(f"\n{'='*60}")
    print("API契约验证结果")
    print(f"{'='*60}")
    print(f"规范文件: {results['spec_file']}")
    print(f"基础URL: {results['base_url']}")
    print(f"验证状态: {'✅ 通过' if results['valid'] else '❌ 失败'}")
    print(f"端点总数: {results['total_endpoints']}")
    
    if results.get('errors'):
        print(f"\n错误 ({len(results['errors'])}):")
        for err in results['errors']:
            print(f"  ❌ {err}")
    
    if results.get('warnings'):
        print(f"\n警告 ({len(results['warnings'])}):")
        for warn in results['warnings']:
            print(f"  ⚠️ {warn}")
    
    print(f"{'='*60}")


def main():
    """主函数"""
    args = parse_args()
    
    parser = OpenAPIParser(args.spec)
    if not parser.load():
        sys.exit(1)
    
    validator = ContractValidator(parser, args.base_url)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'spec_file': args.spec,
        'base_url': args.base_url,
        'valid': True,
        'total_endpoints': len(parser.get_endpoints()),
        'errors': [],
        'warnings': [],
        'checks': []
    }
    
    structure_result = validator.validate_spec_structure()
    results['checks'].append(structure_result)
    if not structure_result['valid']:
        results['valid'] = False
        results['errors'].extend(structure_result['issues'])
    
    endpoint_results = validator.validate_endpoints()
    results['checks'].extend(endpoint_results)
    
    for ep_result in endpoint_results:
        if not ep_result['valid']:
            results['valid'] = False
            results['errors'].extend([f"{ep_result['method']} {ep_result['path']}: {i}" for i in ep_result['issues']])
        if ep_result.get('warnings'):
            results['warnings'].extend([f"{ep_result['method']} {ep_result['path']}: {w}" for w in ep_result['warnings']])
    
    if args.validate_response:
        for endpoint in parser.get_endpoints():
            response_result = validator.validate_response_schema(
                endpoint['path'], endpoint['method'], {'status_code': 200, 'body': {}}
            )
            results['checks'].append(response_result)
            if not response_result['valid']:
                results['valid'] = False
                results['errors'].extend(response_result.get('issues', []))

    if args.check_deprecated:
        deprecated_result = validator.check_deprecated_usage(
            [{'path': ep['path'], 'method': ep['method']} for ep in parser.get_endpoints()]
        )
        results['checks'].append(deprecated_result)
        if deprecated_result.get('deprecated_found'):
            results['warnings'].extend(deprecated_result.get('issues', []))

    generate_report(args.output, results)
    print_summary(results)
    
    if not results['valid']:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
