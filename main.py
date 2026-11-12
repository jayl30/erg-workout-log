from dataclasses import dataclass
from drafter import *
from bakery import assert_equal

set_site_information(
    author = "Jayden Lugo",
    description = "An erg workout log for rowers that calculates 500m split and watts, "
                    "keeps a workout history, and tracks your best 2k.",
    sources = ["Concept 2 watts formula: watts = 2.80 / (seconds per meter) ** 3"],
    planning = ["brainstorm.pdf" , "design.pdf","LLM.pdf"],
    links = ["https://github.com/jayl30/erg-workout-log"]
    )

workout_types = ["Steady State", "Intervals", "Test"]
filter_options = ["All", "Steady State", "Intervals", "Test"]

@dataclass
class Workout:
    distance : int
    time_seconds : int
    stroke_rate : int
    workout_type : str
    
@dataclass
class State:
    username : str
    workouts : list[Workout]
    best_2k_seconds: int
    filter_type : str


def calculate_split(distance : int, time_seconds : int) -> float :
    """Returns the average time in seconds it takes to row 500 meters."""
    return time_seconds / (distance / 500)

assert_equal(calculate_split(2000,480), 120.0)
assert_equal(calculate_split(500,100), 100.0)
assert_equal(calculate_split(1000,210), 105.0)


def calculate_watts(distance : int, time_seconds : int) -> int:
    """Returns the average watts per piece, using the Concept 2 formula."""
    pace = time_seconds / distance
    return round(2.80 / pace ** 3)

assert_equal(calculate_watts(2000, 480), 203)
assert_equal(calculate_watts(500, 100), 350)


def format_time(seconds : float) -> str:
    """ Turns a number of seconds into minutes:seconds string, IE 1:49)"""
    total = round(seconds)
    minutes = total // 60
    seconds_left = total % 60
    if seconds_left < 10:
        return str(minutes) + ":0" + str(seconds_left)
    return str(minutes) + ":" + str(seconds_left)

assert_equal(format_time(120.0), "2:00")
assert_equal(format_time(108.8), "1:49")
assert_equal(format_time(435), "7:15")
assert_equal(format_time(65), "1:05")


def workout_summary(number : int, workout:Workout) -> str:
    """ Returns 1 line of text to describe a workout and its split."""
    split = calculate_split(workout.distance, workout.time_seconds)
    return (str(number) + ". " + workout.workout_type + " - " + str(workout.distance) + "m in "
            + format_time(workout.time_seconds) + " (" + format_time(split) + " /500m, "
            + str(workout.stroke_rate) + " spm)")

assert_equal(workout_summary(1, Workout(2000, 480, 30, "Test")),
             "1. Test - 2000m in 8:00 (2:00 /500m, 30 spm)")

def find_best_2k(workouts: list[Workout]) -> int:
    "iterates over the workouts and returns the fastest 2000m time"
    best = 0
    for workout in workouts:
        if workout.distance == 2000:
            if best == 0 or workout.time_seconds < best :
                best = workout.time_seconds
    return best

assert_equal(find_best_2k([]), 0)
assert_equal(find_best_2k([Workout(5000, 1200, 20, "Steady State")]), 0)
assert_equal(find_best_2k([Workout(2000, 480, 30, "Test"), Workout(2000, 470, 31, "Test")]), 470)


@route
def index(state: State) -> Page:
    """The home page which greets the user and links to each other page"""
    if state.username == "":
        greeting = "Welcome to the Erg Log!"
    else:
        greeting = "Welcome Back, " + state.username + "!"
    return Page(state, [
        Header("Erg Workout Log"),
        greeting,
        "Your name:",
        TextBox("username", state.username),
        Button("Set Name", save_name),
        Button("Log a workout", log_workout),
        Button("Workout History", view_history),
        Button("Stats", view_stats),
        Button("Split calculator", calculator)
    ])

@route
def save_name(state: State, username : str) -> Page:
    """Saves name of user, then returns to home page"""
    state.username = username
    return index(state)

@route
def log_workout(state: State) -> Page:
    """Shows page to log workout"""
    return Page(state, [
        Header("Log a Workout"),
        "Distance (Meters):",
        TextBox("distance"),
        "Time - minutes:",
        TextBox("minutes"),
        "Time - seconds:",
        TextBox("seconds"),
        "Stroke rate (per minute):",
        TextBox("stroke_rate"),
        "Workout type:",
        SelectBox("workout_type", workout_types),
        Button("Save workout", save_workout),
        Button("Home", index)
        ])

@route
def save_workout(state : State, distance : int, minutes : int, seconds : int,
                 stroke_rate: int, workout_type : str) -> Page:
    """saves new workout and shows its split/watts"""
    total_seconds = minutes * 60 + seconds
    state.workouts.append(Workout(distance, total_seconds, stroke_rate, workout_type))
    message = "Workout saved!"
    if distance == 2000 and (state.best_2k_seconds == 0 or total_seconds < state.best_2k_seconds):
        state.best_2k_seconds = total_seconds
        message = "Workout saved! New 2k PR!"
    return Page(state,[
        Header(message),
        "Split: " + format_time(calculate_split(distance, total_seconds)) + " /500m",
        "Average watts: " + str(calculate_watts(distance,total_seconds)),
        Button("Log another", log_workout),
        Button("Workout History", view_history),
        Button("Home",index)
    ])

@route
def view_history(state: State) -> Page:
    """lists the saved workouts that match current filter"""
    content = [Header("Workout History"), "Showing: " + state.filter_type]
    number = 1
    for workout in state.workouts:
        if state.filter_type == "All" or workout.workout_type == state.filter_type:
            content.append(workout_summary(number, workout))
        number += 1
    content.append("Filter by type:")
    content.append(SelectBox("filter_type", filter_options, state.filter_type))
    content.append(Button("Apply filter", apply_filter))
    content.append("Workout number to delete:")
    content.append(TextBox("workout_num"))
    content.append(Button("Delete", delete_workout))
    content.append(Button("Home", index))
    return Page(state,content)


@route
def apply_filter(state : State, filter_type : str) -> Page:
    """changes the type of workout shown in history page"""
    state.filter_type = filter_type
    return view_history(state)

@route
def delete_workout(state : State, workout_num : int) -> Page:
    """Removes the workout with the given number, then updates the best 2k"""
    state.workouts.pop(workout_num -1)
    state.best_2k_seconds = find_best_2k(state.workouts)
    return view_history(state)


@route
def view_stats(state : State) -> Page:
    """Loops over workouts to add up total meters, and shows best 2k"""
    total_meters = 0
    for workout in state.workouts:
        total_meters += workout.distance
    if state.best_2k_seconds == 0:
        best_text = "Best 2k: None"
    else:
        best_text = "Best 2k: " + format_time(state.best_2k_seconds)
    return Page(state, [
        Header("Stats"),
        "Workouts logged: " + str(len(state.workouts)),
        "Total meters: " + str(total_meters),
        best_text,
        Button("Home", index)
    ])

@route
def calculator(state: State) -> Page:
    """Shows a calculator to calculate a split without saving a workout."""
    return Page(state, [
        Header("Split Calculator"),
        "Distance (meters):",
        TextBox("distance"),
        "Time - minutes:",
        TextBox("minutes"),
        "Time - seconds:",
        TextBox("seconds"),
        Button("Calculate", show_split),
        Button("Home", index)
    ])

@route
def show_split(state: State, distance: int, minutes: int, seconds: int) -> Page:
    """Calculates and shows the split and watts for the numbers entered."""
    total_seconds = minutes * 60 + seconds
    return Page(state, [
        Header("Result"),
        "Split: " + format_time(calculate_split(distance, total_seconds)) + " /500m",
        "Average watts: " + str(calculate_watts(distance, total_seconds)),
        Button("Calculate again", calculator),
        Button("Home", index)
    ])



#index
assert_equal(index(State("Jayden", [], 0, "All")), Page(State("Jayden", [], 0, "All"), [
    Header("Erg Workout Log"),
    "Welcome Back, Jayden!",
    "Your name:",
    TextBox("username", "Jayden"),
    Button("Set Name", save_name),
    Button("Log a workout", log_workout),
    Button("Workout History", view_history),
    Button("Stats", view_stats),
    Button("Split calculator", calculator)
]))

#save_name
assert_equal(save_name(State("", [], 0, "All"), "Jayden"),
             index(State("Jayden", [], 0, "All")))

#log_workout
assert_equal(log_workout(State("", [], 0, "All")), Page(State("", [], 0, "All"), [
    Header("Log a Workout"),
    "Distance (Meters):",
    TextBox("distance"),
    "Time - minutes:",
    TextBox("minutes"),
    "Time - seconds:",
    TextBox("seconds"),
    "Stroke rate (per minute):",
    TextBox("stroke_rate"),
    "Workout type:",
    SelectBox("workout_type", workout_types),
    Button("Save workout", save_workout),
    Button("Home", index)
]))

#save_workout
assert_equal(save_workout(State("", [], 470, "All"), 2000, 8, 0, 30, "Test"),
             Page(State("", [Workout(2000, 480, 30, "Test")], 470, "All"), [
                 Header("Workout saved!"),
                 "Split: 2:00 /500m",
                 "Average watts: 203",
                 Button("Log another", log_workout),
                 Button("Workout History", view_history),
                 Button("Home", index)
             ]))

#view_history
assert_equal(view_history(State("", [Workout(2000, 480, 30, "Test"),
                                     Workout(5000, 1250, 20, "Steady State")], 480, "Test")),
             Page(State("", [Workout(2000, 480, 30, "Test"),
                             Workout(5000, 1250, 20, "Steady State")], 480, "Test"), [
                 Header("Workout History"),
                 "Showing: Test",
                 "1. Test - 2000m in 8:00 (2:00 /500m, 30 spm)",
                 "Filter by type:",
                 SelectBox("filter_type", filter_options, "Test"),
                 Button("Apply filter", apply_filter),
                 "Workout number to delete:",
                 TextBox("workout_num"),
                 Button("Delete", delete_workout),
                 Button("Home", index)
             ]))

#apply_filter
assert_equal(apply_filter(State("", [Workout(2000, 480, 30, "Test")], 480, "All"), "Test"),
             view_history(State("", [Workout(2000, 480, 30, "Test")], 480, "Test")))


#delete_workout
assert_equal(delete_workout(State("", [Workout(2000, 480, 30, "Test"),
                                       Workout(5000, 1250, 20, "Steady State")], 480, "All"), 1),
             view_history(State("", [Workout(5000, 1250, 20, "Steady State")], 0, "All")))


#view_stats
assert_equal(view_stats(State("", [Workout(2000, 480, 30, "Test"),
                                   Workout(5000, 1250, 20, "Steady State")], 480, "All")),
             Page(State("", [Workout(2000, 480, 30, "Test"),
                             Workout(5000, 1250, 20, "Steady State")], 480, "All"), [
                 Header("Stats"),
                 "Workouts logged: 2",
                 "Total meters: 7000",
                 "Best 2k: 8:00",
                 Button("Home", index)
             ]))

#calculator
assert_equal(calculator(State("", [], 0, "All")), Page(State("", [], 0, "All"), [
    Header("Split Calculator"),
    "Distance (meters):",
    TextBox("distance"),
    "Time - minutes:",
    TextBox("minutes"),
    "Time - seconds:",
    TextBox("seconds"),
    Button("Calculate", show_split),
    Button("Home", index)
]))


#show_split
assert_equal(show_split(State("", [], 0, "All"), 500, 1, 40),
             Page(State("", [], 0, "All"), [
                 Header("Result"),
                 "Split: 1:40 /500m",
                 "Average watts: 350",
                 Button("Calculate again", calculator),
                 Button("Home", index)
             ]))

start_server(State("", [], 0, "All"))

