import turtle

def draw_circle(t, radius, color):
    t.fillcolor(color)
    t.begin_fill()
    t.circle(radius)
    t.end_fill()

def draw_triangle(t, points, color):
    t.fillcolor(color)
    t.up()
    t.goto(points[0])
    t.down()
    t.begin_fill()
    t.goto(points[1])
    t.goto(points[2])
    t.goto(points[0])
    t.end_fill()

wn = turtle.Screen()
wn.bgcolor("black")

p = turtle.Turtle()
p.speed(3)
p.color("orange")

# Body
p.up()
p.goto(0, -100)
p.down()
draw_circle(p, 100, "red")

# Wing (triangle)
wing_points = [(0, 0), (80, 60), (40, 20)]
draw_triangle(p, wing_points, "yellow")

# Beak (small triangle)
beak_points = [(100, 0), (130, 20), (100, 40)]
draw_triangle(p, beak_points, "yellow")

# Eye (small white circle)
p.up()
p.goto(40, 50)
p.down()
draw_circle(p, 10, "white")

p.hideturtle()
wn.mainloop()