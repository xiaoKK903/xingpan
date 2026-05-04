"""测试 story_card 相关导入"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Testing imports for story_card...")
print("=" * 60)

try:
    print("\n1. Testing app.services.synastry_highlights_service...")
    from app.services.synastry_highlights_service import (
        extract_synastry_highlights,
        analyze_element_compatibility,
        determine_match_type
    )
    print("   ✓ synastry_highlights_service imports OK")
except Exception as e:
    print(f"   ✗ synastry_highlights_service import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n2. Testing app.services.past_life.story_card_service...")
    from app.services.past_life.story_card_service import (
        generate_story_card,
        get_template_list,
        get_rarity_config,
        generate_share_code
    )
    print("   ✓ story_card_service imports OK")
except Exception as e:
    print(f"   ✗ story_card_service import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n3. Testing app.models.chart StoryCard...")
    from app.models.chart import StoryCard, StoryCardRarity, StoryCardTemplate
    print(f"   ✓ StoryCard model OK, table: {StoryCard.__tablename__}")
except Exception as e:
    print(f"   ✗ StoryCard model import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n4. Testing app.routers.story_card...")
    from app.routers import story_card
    print(f"   ✓ story_card router OK, has prefix: /api/story-card")
except Exception as e:
    print(f"   ✗ story_card router import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\n5. Testing app.main full import...")
    from app.main import app
    print("   ✓ app.main imports OK")
    print(f"   - Routes count: {len(app.routes)}")
except Exception as e:
    print(f"   ✗ app.main import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Import test completed!")
print("=" * 60)
