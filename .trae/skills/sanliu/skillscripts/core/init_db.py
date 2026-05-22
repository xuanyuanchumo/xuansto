#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部协同开发系统 - 数据库初始化脚本

初始化数据库表和默认数据，包括：
- 创建所有数据库表
- 初始化三省六部二十四司部门结构

使用示例:
    python init_db.py                      # 初始化数据库
    python init_db.py --reset              # 重置数据库（删除并重建）
    python init_db.py --json               # JSON 格式输出
    python init_db.py --check-only         # 仅检查数据库连接

退出码:
    0 - 成功
    1 - 错误
    2 - 警告
"""

import sys
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from skillscripts.utils.script_utils import (
    ScriptBase, ScriptResult, ExitCode, create_result
)


@dataclass
class InitResult:
    tables_created: int = 0
    departments_created: int = 0
    connection_ok: bool = False
    details: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tables_created": self.tables_created,
            "departments_created": self.departments_created,
            "connection_ok": self.connection_ok,
            "details": self.details
        }


class InitDbScript(ScriptBase):
    DEFAULT_DESCRIPTION = "三省六部协同开发系统 - 数据库初始化脚本"
    DEFAULT_EPILOG = """
示例:
  python init_db.py                      # 初始化数据库
  python init_db.py --reset              # 重置数据库（删除并重建）
  python init_db.py --json               # JSON 格式输出
  python init_db.py --check-only         # 仅检查数据库连接

退出码:
  0 - 成功
  1 - 错误
  2 - 警告
"""
    
    def _add_arguments(self):
        self.parser.add_argument(
            "--reset",
            action="store_true",
            help="重置数据库（删除并重建所有表）"
        )
        self.parser.add_argument(
            "--check-only",
            action="store_true",
            help="仅检查数据库连接，不执行初始化"
        )
    
    def check_connection(self) -> bool:
        try:
            from app.models.base import engine
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False
    
    def init_departments(self) -> int:
        from app.models.base import SessionLocal
        from app.models.department import Department
        
        db = SessionLocal()
        try:
            if db.query(Department).first():
                self.logger.info("部门数据已存在，跳过初始化")
                return 0
            
            departments = [
                {"name": "中书省", "pinyin": "zhongshusheng", "level": "province"},
                {"name": "门下省", "pinyin": "menxiasheng", "level": "province"},
                {"name": "尚书省", "pinyin": "shangshusheng", "level": "province"},
            ]
            
            ministries = [
                {"name": "吏部", "pinyin": "libu", "level": "ministry", "parent_pinyin": "shangshusheng"},
                {"name": "户部", "pinyin": "hubu", "level": "ministry", "parent_pinyin": "shangshusheng"},
                {"name": "礼部", "pinyin": "liibu", "level": "ministry", "parent_pinyin": "shangshusheng"},
                {"name": "兵部", "pinyin": "bingbu", "level": "ministry", "parent_pinyin": "shangshusheng"},
                {"name": "刑部", "pinyin": "xingbu", "level": "ministry", "parent_pinyin": "shangshusheng"},
                {"name": "工部", "pinyin": "gongbu", "level": "ministry", "parent_pinyin": "shangshusheng"},
            ]
            
            divisions = {
                "libu": ["xuansi", "kaosi", "xunsi", "juesi"],
                "hubu": ["duzhisi", "jinbucangsi", "cangbucangsi", "libucangsi"],
                "liibu": ["yibusi", "ciwusi", "shanbucangsi", "kebucangsi"],
                "bingbu": ["yibusi", "zhibusi", "jiabucangsi", "kubucangsi"],
                "xingbu": ["xingbucangsi", "dubucangsi", "bibucangsi", "sibucangsi"],
                "gongbu": ["yingzaosi", "dushuisi", "tuntiansi", "yuhengsi"],
            }
            
            division_names = {
                "xuansi": "选司", "kaosi": "考司", "xunsi": "勋司", "juesi": "爵司",
                "duzhisi": "度支司", "jinbucangsi": "金部仓司", "cangbucangsi": "仓部仓司", "libucangsi": "吏部仓司",
                "yibusi": "仪部司", "ciwusi": "祠部司", "shanbucangsi": "膳部仓司", "kebucangsi": "客部仓司",
                "zhibusi": "职部司", "jiabucangsi": "驾部仓司", "kubucangsi": "库部仓司",
                "xingbucangsi": "刑部仓司", "dubucangsi": "都部仓司", "bibucangsi": "比部仓司", "sibucangsi": "司部仓司",
                "yingzaosi": "营造司", "dushuisi": "都水司", "tuntiansi": "屯田司", "yuhengsi": "虞衡司",
            }
            
            count = 0
            for dept in departments:
                db.add(Department(name=dept["name"], pinyin=dept["pinyin"], level=dept["level"]))
                count += 1
            db.commit()
            
            for ministry in ministries:
                parent = db.query(Department).filter(Department.pinyin == ministry["parent_pinyin"]).first()
                db.add(Department(
                    name=ministry["name"],
                    pinyin=ministry["pinyin"],
                    level=ministry["level"],
                    parent_id=parent.id
                ))
                count += 1
            db.commit()
            
            for ministry_pinyin, division_pinyins in divisions.items():
                parent = db.query(Department).filter(Department.pinyin == ministry_pinyin).first()
                for div_pinyin in division_pinyins:
                    db.add(Department(
                        name=division_names.get(div_pinyin, div_pinyin),
                        pinyin=f"{ministry_pinyin}_{div_pinyin}",
                        level="division",
                        parent_id=parent.id
                    ))
                    count += 1
            db.commit()
            
            self.logger.success(f"部门数据初始化完成: 3省, 6部, 24司")
            return count
            
        finally:
            db.close()
    
    def run(self) -> int:
        result_data = InitResult()
        errors: List[str] = []
        
        try:
            from app.models.base import Base, engine
            from app.config import settings
            
            self.logger.info(f"数据库地址: {settings.DATABASE_URL}")
            
            if self.args.check_only:
                result_data.connection_ok = self.check_connection()
                if result_data.connection_ok:
                    self.logger.success("数据库连接正常")
                    message = "数据库连接检查通过"
                else:
                    errors.append("数据库连接失败")
                    message = "数据库连接检查失败"
                
                result = create_result(
                    success=result_data.connection_ok,
                    message=message,
                    data=result_data,
                    errors=errors,
                    duration_ms=self.get_duration_ms()
                )
            else:
                if self.args.reset:
                    self.logger.info("重置数据库...")
                    Base.metadata.drop_all(bind=engine)
                    result_data.details.append("已删除所有表")
                
                self.logger.info("创建数据库表...")
                Base.metadata.create_all(bind=engine)
                result_data.tables_created = len(Base.metadata.tables)
                result_data.details.append(f"已创建 {result_data.tables_created} 个表")
                self.logger.success(f"数据库表创建完成: {result_data.tables_created} 个")
                
                result_data.connection_ok = True
                result_data.departments_created = self.init_departments()
                
                result = create_result(
                    success=True,
                    message=f"数据库初始化完成: 创建 {result_data.tables_created} 个表, {result_data.departments_created} 个部门",
                    data=result_data,
                    errors=errors,
                    duration_ms=self.get_duration_ms()
                )
            
            if self.args.json:
                self.output_json(result)
            elif self.args.markdown:
                self.output_markdown(result)
            else:
                self.output_console(result)
            
            return ExitCode.EXIT_CODE_SUCCESS.value if result.success else ExitCode.EXIT_CODE_ERROR.value
            
        except Exception as e:
            self.logger.critical(f"数据库初始化失败: {e}")
            errors.append(str(e))
            
            result = create_result(
                success=False,
                message=f"数据库初始化失败: {e}",
                data=result_data,
                errors=errors,
                duration_ms=self.get_duration_ms()
            )
            
            if self.args.json:
                self.output_json(result)
            elif self.args.markdown:
                self.output_markdown(result)
            else:
                self.output_console(result)
            
            return ExitCode.EXIT_CODE_ERROR.value


def main():
    script = InitDbScript()
    return script.execute()


if __name__ == "__main__":
    sys.exit(main())
