import nextcord
from nextcord.ext import commands
from nextcord.ui import Select, View, Button
import motor.motor_asyncio
import os
from datetime import datetime

# --- EXERCISE DATABASE ---
ROUTINES = {
    "Beginner": {
        "Gym": [("Pushups", "3x10"), ("Bicep curls", "3x10"), ("Lateral raises", "3x10"), ("Crunches", "3x10")],
        "Calisthenics": [("Push ups", "3x10"), ("Pull ups", "3x10"), ("Dips", "3x10"), ("Pike push ups", "3x10")]
    },
    "Intermediate": {
        "Gym": {
            "Monday": [("Bicep Curls", "3x10"), ("Hammer Curls", "3x10"), ("Tricep Pushdowns", "3x10"), ("Overhead Extensions", "3x10"), ("Barbell Curls", "3x10")],
            "Tuesday": [("Bicep Curls", "3x10"), ("Hammer Curls", "3x10"), ("Tricep Pushdowns", "3x10"), ("Overhead Extensions", "3x10"), ("Barbell Curls", "3x10")],
            "Wednesday": "Rest Day",
            "Thursday": [("Bench Press", "3x10"), ("Incline DB Press", "3x10"), ("Chest Flys", "3x10"), ("Leg Raises", "3x15"), ("Plank", "60s")],
            "Friday": [("Bench Press", "3x10"), ("Incline DB Press", "3x10"), ("Chest Flys", "3x10"), ("Leg Raises", "3x15"), ("Plank", "60s")],
            "Saturday": [("Back Squats", "3x10"), ("Leg Press", "3x10"), ("Calf Raises", "3x15"), ("Leg Extensions", "3x10")],
            "Sunday": "Rest Day"
        },
        "Calisthenics": {
            "Monday": [("Push ups", "3x10"), ("Inclined push ups", "3x10"), ("Dips", "3x10"), ("Pull ups (close)", "3x10"), ("Pull ups (wide)", "3x10"), ("Muscle ups", "3x10")],
            "Tuesday": [("Push ups", "3x10"), ("Inclined push ups", "3x10"), ("Dips", "3x10"), ("Pull ups (close)", "3x10"), ("Pull ups (wide)", "3x10"), ("Muscle ups", "3x10")],
            "Wednesday": "Rest Day",
            "Thursday": [("Push ups", "3x10"), ("Diamond push ups", "3x10"), ("Plank hold", "30-40s"), ("Crunches", "3x10"), ("Frog stand", "20-30s")],
            "Friday": [("Push ups", "3x10"), ("Diamond push ups", "3x10"), ("Plank hold", "30-40s"), ("Crunches", "3x10"), ("Frog stand", "20-30s")],
            "Saturday": [("Squats", "3x10"), ("Mountain climbers", "3x30"), ("Jog/run", "30 mins")],
            "Sunday": "Rest Day"
        }
    },
    "Hard": {
        "Gym": {
            "Monday": [("Bicep Curls", "4x10"), ("Hammer Curls", "4x10"), ("Tricep Pushdowns", "4x10"), ("Overhead Extensions", "4x10"), ("Barbell Curls", "4x10")],
            "Tuesday": [("Bicep Curls", "4x10"), ("Hammer Curls", "4x10"), ("Tricep Pushdowns", "4x10"), ("Overhead Extensions", "4x10"), ("Barbell Curls", "4x10")],
            "Wednesday": "Rest Day",
            "Thursday": [("Bench Press", "4x10"), ("Incline DB Press", "4x10"), ("Chest Flys", "4x10"), ("Leg Raises", "4x20"), ("Plank", "90s")],
            "Friday": [("Bench Press", "4x10"), ("Incline DB Press", "4x10"), ("Chest Flys", "4x10"), ("Leg Raises", "4x20"), ("Plank", "90s")],
            "Saturday": [("Back Squats", "4x10"), ("Leg Press", "4x10"), ("Calf Raises", "4x20"), ("Leg Extensions", "4x10")],
            "Sunday": "Rest Day"
        },
        "Calisthenics": {
            "Monday": [("Push ups", "4x10"), ("Inclined push ups", "4x10"), ("Dips", "4x10"), ("Pull ups (close)", "4x10"), ("Pull ups (wide)", "4x10"), ("Muscle ups", "4x10")],
            "Tuesday": [("Push ups", "4x10"), ("Inclined push ups", "4x10"), ("Dips", "4x10"), ("Pull ups (close)", "4x10"), ("Pull ups (wide)", "4x10"), ("Muscle ups", "4x10")],
            "Wednesday": "Rest Day",
            "Thursday": [("Push ups", "4x10"), ("Diamond push ups", "4x10"), ("Plank hold", "60s"), ("Crunches", "4x10"), ("Frog stand", "40-50s")],
            "Friday": [("Push ups", "4x10"), ("Diamond push ups", "4x10"), ("Plank hold", "60s"), ("Crunches", "4x10"), ("Frog stand", "40-50s")],
            "Saturday": [("Squats", "4x10"), ("Mountain climbers", "4x30"), ("Jog/run", "45 mins")],
            "Sunday": "Rest Day"
        }
    }
}

class WorkoutCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Connect to your existing Mongo setup
        self.cluster = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.db = self.cluster["GymBotDB"]
        self.users = self.db["user_stats"]

    async def get_user_stage(self, user_id):
        """Logic to determine user rank based on total workouts logged."""
        user = await self.users.find_one({"_id": user_id})
        if not user: return "Beginner", 0
        count = user.get("workout_count", 0)
        
        if count >= 30: return "Hard", count
        if count >= 10: return "Intermediate", count
        return "Beginner", count
    
    @nextcord.slash_command(name="schedule", description="View the weekly Gladiator training split")
    async def schedule(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="📅 Weekly Training Split",
            description="Follow this routine to ensure balanced muscle recovery and maximum gains.",
            color=0x3498db
        )

        # Using the specific split you requested
        schedule_text = (
            "**Monday:** Arms + Chest\n"
            "**Tuesday:** Arms + Chest\n"
            "**Wednesday:** *Rest & Recovery*\n"
            "**Thursday:** Abs\n"
            "**Friday:** Abs\n"
            "**Saturday:** Leg Day\n"
            "**Sunday:** *Rest & Recovery*"
        )

        embed.add_field(name="The Routine", value=schedule_text, inline=False)
        embed.set_footer(text="Consistency is the only shortcut. See you at the gym!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @nextcord.slash_command(name="startworkout", description="Access your level-based training routine")
    async def startworkout(self, interaction: nextcord.Interaction):
        stage, count = await self.get_user_stage(interaction.user.id)
        day_name = datetime.now().strftime("%A")
        
        view = View()
        options = [
            nextcord.SelectOption(label="Gym", emoji="🏋️", description="Weights & Machines"),
            nextcord.SelectOption(label="Calisthenics", emoji="🤸", description="Bodyweight mastery")
        ]
        select = Select(placeholder=f"Rank: {stage} | Day: {day_name}", options=options)

        async def select_callback(itx: nextcord.Interaction):
            path = select.values[0]
            stage_data = ROUTINES[stage][path]

            # Handle Split logic for Int/Hard, fixed logic for Beginner
            if isinstance(stage_data, dict):
                routine = stage_data.get(day_name)
            else:
                routine = stage_data

            embed = nextcord.Embed(title=f"🔥 {stage} {path} Routine", color=0x9B59B6)
            embed.set_footer(text=f"Progress: {count} workouts completed | Stay disciplined.")

            if routine == "Rest Day":
                embed.description = "🛋️ **Rest Day!** Recovery is where the muscle grows. See you tomorrow!"
                return await itx.response.send_message(embed=embed, ephemeral=True)

            # Add mandatory warm-up for higher stages
            if stage in ["Intermediate", "Hard"]:
                embed.add_field(name="🧩 Warm-up", value="└ Stretches (5-10 mins)", inline=False)

            # Populate exercises
            for exercise, sets in routine:
                embed.add_field(name=f"🧩 **{exercise}**", value=f"└ {sets}", inline=False)
            
            # --- Completion Logic ---
            finish_view = View()
            finish_button = Button(label="Complete Workout", style=nextcord.ButtonStyle.green, emoji="✅")

            async def finish_callback(f_itx: nextcord.Interaction):
                await self.users.update_one(
                    {"_id": f_itx.user.id}, 
                    {"$inc": {"workout_count": 1}}, 
                    upsert=True
                )
                
                # Check for Level Up after increment
                new_stage, new_count = await self.get_user_stage(f_itx.user.id)
                
                if new_stage != stage:
                    msg = f"🎊 **LEVEL UP!** You've completed {new_count} workouts and reached the **{new_stage}** stage!"
                else:
                    msg = f"💪 Workout logged! ({new_count} total)"
                
                await f_itx.response.send_message(msg, ephemeral=True)

            finish_button.callback = finish_callback
            finish_view.add_item(finish_button)
            
            await itx.response.send_message(embed=embed, view=finish_view, ephemeral=True)

        select.callback = select_callback
        view.add_item(select)
        await interaction.response.send_message("Choose your focus for today:", view=view, ephemeral=True)




def setup(bot):
    bot.add_cog(WorkoutCog(bot))