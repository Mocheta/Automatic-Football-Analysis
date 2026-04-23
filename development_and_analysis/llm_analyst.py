import os
import anthropic
from dotenv import load_dotenv
from .pdf_reporter import save_pdf
load_dotenv()

SYSTEM_PROMPT = """You are an expert football (soccer) analyst with deep tactical and physical knowledge.
You are given statistical data automatically extracted from a match video using computer vision.
Numbers may not be perfectly precise, but they reflect real tracking data.

Your response must have exactly three sections with these headings:

## Match Overview
2-3 paragraphs describing what likely happened during the match. Reference specific numbers
(possession %, pass accuracy, shots, distance covered, player speeds). Paint a narrative of
how the game unfolded — which team dominated, how intensity varied, who created chances.

## Tips for Team 1
3-5 bullet points with concrete, actionable tactical recommendations based on the stats.
Each bullet must reference at least one specific number from the data.

## Tips for Team 2
3-5 bullet points with concrete, actionable tactical recommendations based on the stats.
Each bullet must reference at least one specific number from the data.

Write in a professional analyst tone. Be direct and specific."""


def _build_prompt(data: dict) -> str:
    lines = ["MATCH STATISTICS\n"]

    p = data.get('possession', {})
    lines.append(f"POSSESSION\n  Team 1: {p.get('team_1_pct', 0):.1f}%\n  Team 2: {p.get('team_2_pct', 0):.1f}%\n")

    f = data.get('formations', {})
    lines.append(f"FORMATIONS\n  Team 1: {f.get('team_1_formation', 'Unknown')}\n  Team 2: {f.get('team_2_formation', 'Unknown')}\n")

    s = data.get('shots', {})
    lines.append(
        f"SHOTS\n"
        f"  Team 1: {s.get('team_1_shots', 0)} shots  ({s.get('team_1_on_target', 0)} on target, {s.get('team_1_off_target', 0)} off target)\n"
        f"  Team 2: {s.get('team_2_shots', 0)} shots  ({s.get('team_2_on_target', 0)} on target, {s.get('team_2_off_target', 0)} off target)\n"
    )

    ps = data.get('passes', {})
    lines.append(
        f"PASSES & TURNOVERS\n"
        f"  Team 1: {ps.get('team_1_passes', 0)} passes, {ps.get('team_1_turnovers', 0)} turnovers, {ps.get('team_1_accuracy', 0):.1f}% accuracy\n"
        f"  Team 2: {ps.get('team_2_passes', 0)} passes, {ps.get('team_2_turnovers', 0)} turnovers, {ps.get('team_2_accuracy', 0):.1f}% accuracy\n"
        f"  Avg pass duration: {ps.get('avg_pass_duration', 0):.1f} frames\n"
    )

    player_stats = data.get('player_stats', {})
    if player_stats:
        for team_id in [1, 2]:
            lines.append(f"PLAYER STATS — Team {team_id}")
            team_players = {pid: s for pid, s in player_stats.items() if s.get('team') == team_id}
            for pid, s in sorted(team_players.items()):
                lines.append(
                    f"  Player {pid}: {s['total_distance']:.0f}m covered, "
                    f"{s['top_speed']:.1f} km/h top speed, "
                    f"{s['possession_frames'] / 24:.1f}s on ball"
                )
            lines.append("")

    return "\n".join(lines)


def generate_report(stats_filepath: str, structured_data: dict = None,
                    output_filepath: str = None) -> str:
    """Call Claude to analyse the match and write a report.

    If structured_data is provided it is used directly (cleaner input).
    Otherwise the stats text file is read as a fallback.
    """
    if structured_data is not None:
        user_content = _build_prompt(structured_data)
    else:
        with open(stats_filepath, 'r') as f:
            user_content = f.read()

    if output_filepath is None:
        output_filepath = stats_filepath.replace('Stats_', 'Analysis_')

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                "Here are the match statistics extracted from video analysis:\n\n"
                f"{user_content}\n\n"
                "Please provide the match overview and tactical tips for both teams."
            )
        }]
    ) as stream:
        final_message = stream.get_final_message()

    analysis = next(
        (block.text for block in final_message.content if block.type == "text"),
        ""
    )

    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("AI MATCH ANALYSIS  (powered by Claude)\n")
        f.write("=" * 80 + "\n\n")
        f.write(analysis)
        f.write("\n")

    print(f"[LLMAnalyst] Analysis saved to {output_filepath}")

    if structured_data is not None:
        match_name = output_filepath.replace('Analysis_', '').replace('.txt', '')
        match_name = match_name.split('/')[-1].split('\\')[-1]
        pdf_path = output_filepath.replace('Analysis_', 'Report_').replace('.txt', '.pdf')
        save_pdf(pdf_path, match_name, structured_data, analysis)

    return analysis
