import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "skillscripts" / "utils"))

try:
    from enhanced_path_config_manager import EnhancedSkillPathManager
except ImportError:
    from skillscripts.utils.enhanced_path_config_manager import EnhancedSkillPathManager

path_manager = EnhancedSkillPathManager.get_instance()
base_dir = path_manager.skill_root

files_to_check = {
    'SKILL.md': [
        'subskills/baihehua_liushuixian.md',
        'zhongshusheng/SKILL.md',
        'menxiasheng/SKILL.md',
        'shangshusheng/SKILL.md',
        'shangshusheng/libu/SKILL.md',
        'shangshusheng/hubu/SKILL.md',
        'shangshusheng/liibu/SKILL.md',
        'shangshusheng/bingbu/SKILL.md',
        'shangshusheng/xingbu/SKILL.md',
        'shangshusheng/gongbu/SKILL.md',
        'subskills/tdd_liucheng.md',
        'subskills/sdd_liucheng.md',
        'subskills/huanjing_jiance.md',
        'subskills/jiagou_yuanze.md',
        'subskills/toumingdu_yanzheng.md',
        'subskills/ceshi.md',
        'subskills/waiji_jicheng.md',
        'resources/templates/sdd_guifan_muban.md',
        'resources/templates/sdd_xiangmu.md',
        'resources/templates/web_xiangmu.md',
        'resources/templates/ai_xiangmu.md',
        'resources/templates/mcp_fuwuqi.md',
        'resources/ceshi_muban.md',
        'resources/bingbu_ceshi_muban.md',
        'resources/api_sheji_muban.md',
        'resources/shujuku_sheji_muban.md',
        'resources/daima_guifan.md',
        'resources/tdd_guifan.md',
        'resources/anquan_guifan.md',
        'resources/waiji_zhuce_muban.md',
        'resources/waiji_zhuce_biao.md',
        'resources/wenti_genzong_muban.md',
        'resources/daima_yiwei_qingdan.md',
        'resources/workflow_zhuangtai.md',
        'resources/best_practices/tdd_shijian.md',
        'resources/best_practices/sdd_shijian.md',
        'resources/best_practices/tuandui_xiezuo.md',
        'resources/best_practices/xiangmu_qidong.md',
        'subskills/bushu.md',
    ],
    'menxiasheng/SKILL.md': [
        '../subskills/daima_shencha.md',
        '../resources/daima_guifan.md',
        '../scripts/record_skill_call.py',
        '../subskills/rengong_queren.md',
    ],
    'zhongshusheng/SKILL.md': [
        '../subskills/xuqiu_fenxi.md',
        '../subskills/xuqiu_jiegouhua.md',
        '../subskills/xiangmu_guihua.md',
        '../subskills/xitong_sheji.md',
        '../subskills/yan_shou_ceshi.md',
        '../scripts/record_skill_call.py',
        '../subskills/sdd_liucheng.md',
        '../subskills/guifan_jiexi.md',
    ],
    'shangshusheng/SKILL.md': [
        '../subskills/waiji_jicheng.md',
        '../subskills/baihehua_liushuixian.md',
        '../scripts/record_skill_call.py',
    ],
    'shangshusheng/libu/SKILL.md': [
        'xuansi/SKILL.md',
        '../../scripts/assign_agent.py',
        '../../scripts/record_skill_call.py',
    ],
    'shangshusheng/hubu/SKILL.md': [
        '../../scripts/record_skill_call.py',
    ],
    'shangshusheng/liibu/SKILL.md': [
        '../../resources/daima_guifan.md',
        '../../resources/tdd_guifan.md',
        '../../resources/api_sheji_muban.md',
        '../../resources/shujuku_sheji_muban.md',
        '../../resources/ceshi_muban.md',
        '../../scripts/record_skill_call.py',
        '../../resources/waiji_zhuce_biao.md',
    ],
    'shangshusheng/bingbu/SKILL.md': [
        '../../subskills/huanjing_jiance.md',
        'subskills/sdd_liucheng.md',
        '../../resources/ceshi_muban.md',
        '../../subskills/ceshi_yongli_sheji.md',
        '../../subskills/ceshi.md',
        '../../subskills/anquan_ceshi.md',
        '../../subskills/tubian_ceshi.md',
        '../../subskills/sdd_liucheng.md',
    ],
    'shangshusheng/xingbu/SKILL.md': [
        '../../subskills/wenti_xiufu.md',
        '../../subskills/daima_chonggou.md',
        '../../subskills/jiagou_yuanze.md',
        '../../subskills/xingneng_youhua.md',
        '../../scripts/record_skill_call.py',
        '../../subskills/guifan_yanzheng.md',
        '../../resources/daima_yiwei_qingdan.md',
        '../../resources/wenti_genzong_muban.md',
    ],
    'shangshusheng/gongbu/SKILL.md': [
        'yingzaosi/SKILL.md',
        'dushuisi/SKILL.md',
        'tuntiansi/SKILL.md',
        '../../subskills/jiagou_yuanze.md',
        '../../scripts/record_skill_call.py',
        '../../subskills/tdd_liucheng.md',
        '../../subskills/sdd_liucheng.md',
        '../../subskills/ui_ux_sheji.md',
        '../../subskills/api_sheji.md',
        '../../subskills/shujuku_sheji.md',
        '../../subskills/daima_shengcheng.md',
        '../../subskills/sdd_tdd_ronghe.md',
    ],
    'shangshusheng/gongbu/dushuisi/SKILL.md': [
        '../../../scripts/record_skill_call.py',
        '../../../resources/api_sheji_muban.md',
    ],
    'shangshusheng/gongbu/tuntiansi/SKILL.md': [
        '../../../scripts/record_skill_call.py',
        '../../../resources/shujuku_sheji_muban.md',
    ],
    'shangshusheng/gongbu/yingzaosi/SKILL.md': [
        '../../../scripts/record_skill_call.py',
    ],
    'shangshusheng/gongbu/yuhengsi/SKILL.md': [
        '../../../scripts/record_skill_call.py',
    ],
    'shangshusheng/libu/xuansi/SKILL.md': [
        '../../../scripts/record_skill_call.py',
    ],
}

valid_refs = []
invalid_refs = []

for file_path, refs in files_to_check.items():
    file_dir = base_dir / file_path
    if not file_dir.exists():
        continue
    
    file_dir = file_dir.parent
    
    for ref in refs:
        if ref.startswith('../'):
            target_path = (file_dir / ref).resolve()
        elif ref.startswith('./'):
            target_path = (file_dir / ref[2:]).resolve()
        else:
            target_path = (file_dir / ref).resolve()
        
        exists = target_path.exists()
        
        ref_info = {
            'source_file': file_path,
            'reference': ref,
            'resolved_path': str(target_path.relative_to(base_dir)) if exists else str(target_path),
            'exists': exists
        }
        
        if exists:
            valid_refs.append(ref_info)
        else:
            invalid_refs.append(ref_info)

print('=' * 80)
print(f'有效引用路径 (共{len(valid_refs)}个)')
print('=' * 80)
for ref in valid_refs:
    print(f"[OK] {ref['source_file']} -> {ref['reference']}")

print()
print('=' * 80)
print(f'无效引用路径 (断链) (共{len(invalid_refs)}个)')
print('=' * 80)
for ref in invalid_refs:
    print(f"[FAIL] {ref['source_file']} -> {ref['reference']}")
    print(f"  解析路径: {ref['resolved_path']}")
    print()
