#!/usr/bin/env python3
"""Check agent health and accessibility."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.my_util import my_a2a


async def check_agent(url: str, name: str):
    """Check if an agent is accessible and return its card."""
    print(f"\n{'=' * 60}")
    print(f"Checking {name} at {url}")
    print(f"{'=' * 60}")

    try:
        card = await my_a2a.get_agent_card(url)
        if card:
            print(f"✅ {name} is accessible!")
            print(f"   Name: {card.name}")
            print(f"   URL: {card.url}")
            print(f"   Version: {card.version}")
            print(f"   Description: {card.description}")
            print(f"   Skills: {len(card.skills)}")
            if card.skills:
                for skill in card.skills:
                    print(f"     - {skill.name} ({skill.id})")
            return True
        else:
            print(f"❌ {name} returned None")
            return False
    except Exception as e:
        print(f"❌ {name} is NOT accessible")
        print(f"   Error: {e}")
        return False


async def test_message_sending(
    from_url: str, to_url: str, from_name: str, to_name: str
):
    """Test sending a message between agents."""
    print(f"\n{'=' * 60}")
    print(f"Testing message: {from_name} → {to_name}")
    print(f"{'=' * 60}")

    test_message = "Test message: Calculate beam deflection for 2m span, 100kN load"

    try:
        response = await my_a2a.send_message(to_url, test_message)
        result = getattr(response, "result", None)
        if result:
            parts = getattr(result, "parts", None)
            if parts:
                response_text = "\n".join(
                    getattr(part, "text", str(part)) for part in parts
                )
                print("✅ Message sent successfully!")
                print(f"   Response preview: {response_text[:100]}...")
                return True
        print("✅ Message sent, but response format unexpected")
        print(f"   Response: {response}")
        return True
    except Exception as e:
        print("❌ Failed to send message")
        print(f"   Error: {e}")
        return False


async def main():
    """Check all agent endpoints."""
    print("Agent Health Check")
    print("=" * 60)

    # Check local green agent
    local_green = await check_agent("http://localhost:9001", "Green Agent (Local)")

    # Check public green agent
    public_green = await check_agent(
        "https://green.mechgaia.org", "Green Agent (Public)"
    )

    # Check local white agent (on port 9003)
    local_white = await check_agent("http://localhost:9003", "White Agent (Local)")

    # Check controller (on port 9002)
    local_controller = await check_agent("http://localhost:9002", "Controller (Local)")

    # Check public controller/white agent (via Cloudflare)
    public_white = await check_agent(
        "https://white.mechgaia.org", "Controller/White Agent (Public)"
    )

    # Test message sending via Cloudflare if both public agents are available
    cloudflare_test = False
    if public_green and public_white:
        print("\n" + "=" * 60)
        print("Testing Cloudflare Communication")
        print("=" * 60)
        cloudflare_test = await test_message_sending(
            "https://green.mechgaia.org",
            "https://white.mechgaia.org",
            "Green Agent (Public)",
            "White Agent (Public)",
        )

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    print(f"Green Agent (Local):   {'✅ OK' if local_green else '❌ FAIL'}")
    print(
        f"Green Agent (Public):  {'✅ OK' if public_green else '❌ FAIL (cloudflared not running?)'}"
    )
    print(
        f"White Agent (Local):   {'✅ OK' if local_white else '❌ FAIL (not running on port 9003?)'}"
    )
    print(
        f"Controller (Local):    {'✅ OK' if local_controller else '❌ FAIL (not running on port 9002?)'}"
    )
    print(
        f"Controller (Public):   {'✅ OK' if public_white else '❌ FAIL (cloudflared not running?)'}"
    )
    if cloudflare_test:
        print(f"Cloudflare Communication: {'✅ OK' if cloudflare_test else '❌ FAIL'}")

    if not public_green or not public_white:
        print("\n⚠️  Public URLs are not accessible.")
        print("   This is expected if cloudflared is not running.")
        print("   To fix: Run 'python main.py run-ctrl' in a separate terminal")

    return 0 if local_green else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
