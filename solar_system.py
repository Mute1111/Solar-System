import pygame
import sys
import math
import random
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, List

pygame.init()

WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Solar System Simulation")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SUN_COLOR = (255, 255, 190)
PLANET_COLORS = [
    (170, 170, 170),
    (230, 230, 230),
    (50, 100, 200),
    (200, 100, 50),
    (220, 180, 130),
    (220, 190, 150),
    (180, 210, 230),
    (100, 150, 230),
]
DWARF_PLANET_COLORS = {
    "Pluto": (200, 100, 100),
    "Eris": (180, 180, 180),
    "Haumea": (230, 230, 230),
    "Makemake": (200, 120, 120),
    "Quaoar": (150, 150, 150),
    "Orcus": (160, 160, 160),
    "Ceres": (170, 170, 170),
    "Gonggong": (190, 100, 100),
    "Sedna": (200, 80, 80),
    "Salacia": (140, 140, 140),
}
MOON_COLOR = (200, 200, 200)

font = pygame.font.SysFont('Arial', 14)
facts_font = pygame.font.SysFont('Arial', 14)

@dataclass
class CelestialBody:
    x: float
    y: float
    radius: float
    color: Tuple[int, int, int]
    semi_major_axis: float
    eccentricity: float
    angle: float
    base_orbit_speed: float
    orbit_speed: float
    parent: 'CelestialBody' = None
    name: str = ""
    mass: float = 0.0
    facts: Dict[str, str] = None
    orbit_surface: Optional[pygame.Surface] = None
    orbit_rect: Optional[pygame.Rect] = None
    orbit_points: Optional[List[Tuple[float, float]]] = None
    label_surface: Optional[pygame.Surface] = None
    facts_surface: Optional[pygame.Surface] = None
    one_minus_e2: float = 0.0
    last_zoom: float = 0.0
    last_width: int = 0
    last_height: int = 0
    last_view_x: float = 0.0
    last_view_y: float = 0.0

    def update(self):
        self.angle = (self.angle + self.orbit_speed) % (2 * math.pi)
        if self.parent:
            M = self.angle
            E = M
            for _ in range(5):
                E = M + self.eccentricity * math.sin(E)
            sqrt_one_plus_e = math.sqrt(1 + self.eccentricity)
            sqrt_one_minus_e = math.sqrt(1 - self.eccentricity)
            nu = 2 * math.atan2(sqrt_one_plus_e * math.sin(E / 2), sqrt_one_minus_e * math.cos(E / 2))
            r = self.semi_major_axis * self.one_minus_e2 / (1 + self.eccentricity * math.cos(nu))
            self.x = self.parent.x + r * math.cos(nu)
            self.y = self.parent.y + r * math.sin(nu)

    def update_orbit_surface(self, zoom, view_x, view_y, width, height):
        if not self.parent:
            return
        if (self.orbit_surface and
            abs(zoom - self.last_zoom) < 0.01 and
            width == self.last_width and
            height == self.last_height and
            abs(view_x - self.last_view_x) < 1 and
            abs(view_y - self.last_view_y) < 1):
            return
        self.last_zoom = zoom
        self.last_width = width
        self.last_height = height
        self.last_view_x = view_x
        self.last_view_y = view_y

        b = self.semi_major_axis * math.sqrt(self.one_minus_e2)
        self.orbit_points = []
        for t in range(30):
            theta = 2 * math.pi * t / 29
            x = self.semi_major_axis * math.cos(theta)
            y = b * math.sin(theta)
            self.orbit_points.append((x, y))

        parent_x = self.parent.x if self.parent else 0
        parent_y = self.parent.y if self.parent else 0
        screen_points = [
            ((x + parent_x - view_x) * zoom + width // 2,
             (y + parent_y - view_y) * zoom + height // 2)
            for x, y in self.orbit_points
        ]
        xs, ys = zip(*screen_points)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        box_width = int(max_x - min_x) + 2
        box_height = int(max_y - min_y) + 2
        box_width = max(1, min(box_width, width))
        box_height = max(1, min(box_height, height))

        self.orbit_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        self.orbit_rect = pygame.Rect(int(min_x), int(min_y), box_width, box_height)

        orbit_color = (50, 50, 50, 64)
        line_width = 2 if self.semi_major_axis > 10 else 1
        local_points = [
            (x - min_x, y - min_y) for x, y in screen_points
        ]
        pygame.draw.lines(self.orbit_surface, orbit_color, True, local_points, line_width)

    def update_facts_surface(self, width, height):
        if self.facts_surface or not self.facts:
            return
        lines = [
            f"{key}: {value}" for key, value in self.facts.items()
        ]
        max_width = 0
        line_surfaces = []
        for line in lines:
            surf = facts_font.render(line, True, WHITE)
            line_surfaces.append(surf)
            max_width = max(max_width, surf.get_width())
        box_width = max_width + 24
        box_height = len(lines) * 20 + 24
        self.facts_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(self.facts_surface, (0, 0, 0, 128), (0, 0, box_width, box_height), border_radius=6)
        for i, surf in enumerate(line_surfaces):
            self.facts_surface.blit(surf, (12, 12 + i * 20))

    def draw(self, surface, zoom, view_x, view_y, width, height):
        scaled_x = (self.x - view_x) * zoom + width // 2
        scaled_y = (self.y - view_y) * zoom + height // 2
        scaled_radius = self.radius * zoom

        margin = 0.5 * max(width, height)
        if (scaled_x < -margin or scaled_x > width + margin or
            scaled_y < -margin or scaled_y > height + margin):
            return

        if self.parent:
            if self.parent.name != "Sun":
                b = self.semi_major_axis * math.sqrt(self.one_minus_e2)
                points = []
                for t in range(30):
                    theta = 2 * math.pi * t / 29
                    x = self.semi_major_axis * math.cos(theta)
                    y = b * math.sin(theta)
                    screen_x = (x + self.parent.x - view_x) * zoom + width // 2
                    screen_y = (y + self.parent.y - view_y) * zoom + height // 2
                    points.append((int(screen_x), int(screen_y)))
                pygame.draw.lines(surface, (50, 50, 50, 64), True, points, 1)
            else:
                self.update_orbit_surface(zoom, view_x, view_y, width, height)
                if self.orbit_surface:
                    surface.blit(self.orbit_surface, self.orbit_rect)

        pygame.draw.circle(surface, self.color, (int(scaled_x), int(scaled_y)), max(1, int(scaled_radius)))

        if self.name and scaled_radius > 1:
            if self.label_surface is None:
                self.label_surface = font.render(self.name, True, WHITE)
            offset_y = -scaled_radius - 15 if scaled_y < height // 2 else scaled_radius + 5
            surface.blit(self.label_surface, (int(scaled_x - self.label_surface.get_width() // 2), int(scaled_y + offset_y)))

class SolarSystem:
    def __init__(self):
        self.bodies = []
        self.stars = []
        self.planets = []
        self.moons = []
        self.time_factor = 1.0

    def add_star(self, x, y, radius, color, name="", mass=0.0, facts=None):
        star = CelestialBody(
            x=x, y=y, radius=radius, color=color,
            semi_major_axis=0, eccentricity=0, angle=0, base_orbit_speed=0, orbit_speed=0,
            name=name, mass=mass, one_minus_e2=1.0, facts=facts
        )
        self.bodies.append(star)
        self.stars.append(star)
        return star

    def add_planet(self, parent, semi_major_axis, radius, color, orbit_speed, eccentricity, name="", mass=0.0, facts=None):
        angle = random.uniform(0, 2 * math.pi)
        one_minus_e2 = 1 - eccentricity * eccentricity
        planet = CelestialBody(
            x=parent.x, y=parent.y, radius=radius, color=color,
            semi_major_axis=semi_major_axis, eccentricity=eccentricity, angle=angle,
            base_orbit_speed=orbit_speed, orbit_speed=orbit_speed,
            parent=parent, name=name, mass=mass, one_minus_e2=one_minus_e2, facts=facts
        )
        self.bodies.append(planet)
        self.planets.append(planet)
        return planet

    def add_moon(self, parent, semi_major_axis, radius, orbit_speed, eccentricity, name="", mass=0.0, facts=None):
        angle = random.uniform(0, 2 * math.pi)
        one_minus_e2 = 1 - eccentricity * eccentricity
        min_orbit = parent.radius * 2 if parent.name != "Sun" else semi_major_axis
        semi_major_axis = max(semi_major_axis, min_orbit)
        moon = CelestialBody(
            x=parent.x, y=parent.y, radius=radius, color=MOON_COLOR,
            semi_major_axis=semi_major_axis, eccentricity=eccentricity, angle=angle,
            base_orbit_speed=orbit_speed, orbit_speed=orbit_speed,
            parent=parent, name=name, mass=mass, one_minus_e2=one_minus_e2, facts=facts
        )
        self.bodies.append(moon)
        self.moons.append(moon)
        return moon

    def update(self):
        for body in self.bodies:
            if body.parent:
                body.orbit_speed = body.base_orbit_speed * self.time_factor
            body.update()

    def draw(self, surface, zoom, view_x, view_y, width, height):
        for body in self.bodies:
            body.draw(surface, zoom, view_x, view_y, width, height)

def create_real_solar_system(width, height):
    solar_system = SolarSystem()
    center_x, center_y = width // 2, height // 2

    distance_scale = 1.335e-7
    sun_pixel_radius = 5

    planets = [
        {
            "name": "Sun",
            "mass": 1.989e30,
            "radius": 696340,
            "orbit_radius": 0,
            "orbital_period": 0,
            "eccentricity": 0.0,
            "color": SUN_COLOR,
            "facts": {
                "Radius": "696340 km",
                "Composition": "Hydrogen (73.5%), Helium (24%) plasma",
                "Discovery": "Prehistoric",
                "Missions": "Parker Solar Probe (2018–present)",
                "Trivia": "Contains 99.86% of Solar System's mass"
            }
        },
        {
            "name": "Mercury",
            "mass": 3.301e23,
            "radius": 2439.7,
            "orbit_radius": 57.91e6,
            "orbital_period": 87.97,
            "eccentricity": 0.2056,
            "color": PLANET_COLORS[0],
            "facts": {
                "Radius": "2439.7 km",
                "Composition": "Rock (silicates, iron core)",
                "Discovery": "Prehistoric",
                "Missions": "Mariner 10 (1974–75), MESSENGER (2011–15)",
                "Trivia": "Highest orbital eccentricity of planets"
            }
        },
        {
            "name": "Venus",
            "mass": 4.867e24,
            "radius": 6051.8,
            "orbit_radius": 108.21e6,
            "orbital_period": 224.70,
            "eccentricity": 0.0067,
            "color": PLANET_COLORS[1],
            "facts": {
                "Radius": "6051.8 km",
                "Composition": "Rock (silicates, carbon dioxide atmosphere)",
                "Discovery": "Prehistoric",
                "Missions": "Venera (1961–84), Magellan (1990–94)",
                "Trivia": "Hottest planet due to greenhouse effect"
            }
        },
        {
            "name": "Earth",
            "mass": 5.972e24,
            "radius": 6371,
            "orbit_radius": 149.60e6,
            "orbital_period": 365.26,
            "eccentricity": 0.0167,
            "color": PLANET_COLORS[2],
            "facts": {
                "Radius": "6371 km",
                "Composition": "Rock (silicates, iron core), water",
                "Discovery": "Prehistoric",
                "Missions": "Apollo, ISS (1998–present)",
                "Trivia": "Only known planet with life"
            }
        },
        {
            "name": "Mars",
            "mass": 6.417e23,
            "radius": 3389.5,
            "orbit_radius": 227.94e6,
            "orbital_period": 686.98,
            "eccentricity": 0.0934,
            "color": PLANET_COLORS[3],
            "moons": [
                {
                    "name": "Phobos",
                    "mass": 1.066e16,
                    "radius": 11.1,
                    "orbit_radius": 9377,
                    "orbital_period": 0.319,
                    "eccentricity": 0.0151,
                    "facts": {
                        "Radius": "11.1 km",
                        "Composition": "Rock, regolith",
                        "Discovery": "1877 (Asaph Hall)",
                        "Missions": "Mars rovers (imagery)",
                        "Trivia": "Will crash into Mars in ~50M years"
                    }
                },
                {
                    "name": "Deimos",
                    "mass": 1.471e15,
                    "radius": 6.2,
                    "orbit_radius": 23460,
                    "orbital_period": 1.263,
                    "eccentricity": 0.0002,
                    "facts": {
                        "Radius": "6.2 km",
                        "Composition": "Rock, regolith",
                        "Discovery": "1877 (Asaph Hall)",
                        "Missions": "Mars rovers (imagery)",
                        "Trivia": "Smallest moon of Mars"
                    }
                }
            ],
            "facts": {
                "Radius": "3389.5 km",
                "Composition": "Rock (silicates, iron oxide)",
                "Discovery": "Prehistoric",
                "Missions": "Viking (1976), Perseverance (2021–present)",
                "Trivia": "Has the largest volcano (Olympus Mons)"
            }
        },
        {
            "name": "Jupiter",
            "mass": 1.898e27,
            "radius": 69911,
            "orbit_radius": 778.57e6,
            "orbital_period": 4332.59,
            "eccentricity": 0.0489,
            "color": PLANET_COLORS[4],
            "moons": [
                {
                    "name": "Io",
                    "mass": 8.932e22,
                    "radius": 1821.6,
                    "orbit_radius": 421800,
                    "orbital_period": 1.769,
                    "eccentricity": 0.0041,
                    "facts": {
                        "Radius": "1821.6 km",
                        "Composition": "Rock, sulfur",
                        "Discovery": "1610 (Galileo)",
                        "Missions": "Voyager, Galileo",
                        "Trivia": "Most volcanically active body"
                    }
                },
                {
                    "name": "Europa",
                    "mass": 4.800e22,
                    "radius": 1560.8,
                    "orbit_radius": 671100,
                    "orbital_period": 3.551,
                    "eccentricity": 0.0094,
                    "facts": {
                        "Radius": "1560.8 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1610 (Galileo)",
                        "Missions": "Voyager, Galileo, Europa Clipper (2024)",
                        "Trivia": "Possible subsurface ocean"
                    }
                },
                {
                    "name": "Ganymede",
                    "mass": 1.482e23,
                    "radius": 2631.2,
                    "orbit_radius": 1070400,
                    "orbital_period": 7.155,
                    "eccentricity": 0.0013,
                    "facts": {
                        "Radius": "2631.2 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1610 (Galileo)",
                        "Missions": "Voyager, Galileo",
                        "Trivia": "Largest moon in Solar System"
                    }
                },
                {
                    "name": "Callisto",
                    "mass": 1.076e23,
                    "radius": 2410.3,
                    "orbit_radius": 1882700,
                    "orbital_period": 16.689,
                    "eccentricity": 0.0074,
                    "facts": {
                        "Radius": "2410.3 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1610 (Galileo)",
                        "Missions": "Voyager, Galileo",
                        "Trivia": "Most heavily cratered moon"
                    }
                }
            ],
            "facts": {
                "Radius": "69911 km",
                "Composition": "Gas (hydrogen, helium)",
                "Discovery": "Prehistoric",
                "Missions": "Voyager, Juno (2016–present)",
                "Trivia": "Largest planet, Great Red Spot"
            }
        },
        {
            "name": "Saturn",
            "mass": 5.683e26,
            "radius": 58232,
            "orbit_radius": 1433.53e6,
            "orbital_period": 10759.22,
            "eccentricity": 0.0565,
            "color": PLANET_COLORS[5],
            "moons": [
                {
                    "name": "Mimas",
                    "mass": 3.751e19,
                    "radius": 198.2,
                    "orbit_radius": 185540,
                    "orbital_period": 0.942,
                    "eccentricity": 0.0196,
                    "facts": {
                        "Radius": "198.2 km",
                        "Composition": "Ice",
                        "Discovery": "1789 (William Herschel)",
                        "Missions": "Cassini",
                        "Trivia": "Herschel Crater resembles Death Star"
                    }
                },
                {
                    "name": "Enceladus",
                    "mass": 1.080e20,
                    "radius": 252.1,
                    "orbit_radius": 238040,
                    "orbital_period": 1.370,
                    "eccentricity": 0.0047,
                    "facts": {
                        "Radius": "252.1 km",
                        "Composition": "Ice, possible subsurface ocean",
                        "Discovery": "1789 (William Herschel)",
                        "Missions": "Cassini",
                        "Trivia": "Geysers eject water vapor"
                    }
                },
                {
                    "name": "Tethys",
                    "mass": 6.174e20,
                    "radius": 531.1,
                    "orbit_radius": 294670,
                    "orbital_period": 1.888,
                    "eccentricity": 0.0001,
                    "facts": {
                        "Radius": "531.1 km",
                        "Composition": "Ice",
                        "Discovery": "1684 (Cassini)",
                        "Missions": "Cassini",
                        "Trivia": "Features Ithaca Chasma"
                    }
                },
                {
                    "name": "Dione",
                    "mass": 1.095e21,
                    "radius": 561.7,
                    "orbit_radius": 377420,
                    "orbital_period": 2.737,
                    "eccentricity": 0.0022,
                    "facts": {
                        "Radius": "561.7 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1684 (Cassini)",
                        "Missions": "Cassini",
                        "Trivia": "Wispy terrain on trailing hemisphere"
                    }
                },
                {
                    "name": "Rhea",
                    "mass": 2.307e21,
                    "radius": 763.8,
                    "orbit_radius": 527070,
                    "orbital_period": 4.518,
                    "eccentricity": 0.001,
                    "facts": {
                        "Radius": "763.8 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1672 (Cassini)",
                        "Missions": "Cassini",
                        "Trivia": "Second-largest Saturnian moon"
                    }
                },
                {
                    "name": "Titan",
                    "mass": 1.345e23,
                    "radius": 2574.7,
                    "orbit_radius": 1221870,
                    "orbital_period": 15.945,
                    "eccentricity": 0.0288,
                    "facts": {
                        "Radius": "2574.7 km",
                        "Composition": "Ice, rock, methane atmosphere",
                        "Discovery": "1655 (Christiaan Huygens)",
                        "Missions": "Cassini-Huygens",
                        "Trivia": "Only moon with stable lakes"
                    }
                },
                {
                    "name": "Iapetus",
                    "mass": 1.806e21,
                    "radius": 734.5,
                    "orbit_radius": 3560840,
                    "orbital_period": 79.330,
                    "eccentricity": 0.0283,
                    "facts": {
                        "Radius": "734.5 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1671 (Cassini)",
                        "Missions": "Cassini",
                        "Trivia": "Two-toned coloration"
                    }
                }
            ],
            "facts": {
                "Radius": "58232 km",
                "Composition": "Gas (hydrogen, helium)",
                "Discovery": "Prehistoric",
                "Missions": "Cassini (2004–2017)",
                "Trivia": "Famous for prominent rings"
            }
        },
        {
            "name": "Uranus",
            "mass": 8.681e25,
            "radius": 25362,
            "orbit_radius": 2872.46e6,
            "orbital_period": 30589.00,
            "eccentricity": 0.0457,
            "color": PLANET_COLORS[6],
            "moons": [
                {
                    "name": "Miranda",
                    "mass": 6.590e19,
                    "radius": 235.8,
                    "orbit_radius": 129900,
                    "orbital_period": 1.413,
                    "eccentricity": 0.0013,
                    "facts": {
                        "Radius": "235.8 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1948 (Gerard Kuiper)",
                        "Missions": "Voyager 2",
                        "Trivia": "Extreme geological features"
                    }
                },
                {
                    "name": "Ariel",
                    "mass": 1.353e21,
                    "radius": 578.9,
                    "orbit_radius": 190900,
                    "orbital_period": 2.520,
                    "eccentricity": 0.0012,
                    "facts": {
                        "Radius": "578.9 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1851 (William Lassell)",
                        "Missions": "Voyager 2",
                        "Trivia": "Brightest Uranian moon"
                    }
                },
                {
                    "name": "Umbriel",
                    "mass": 1.172e21,
                    "radius": 584.7,
                    "orbit_radius": 266000,
                    "orbital_period": 4.144,
                    "eccentricity": 0.0039,
                    "facts": {
                        "Radius": "584.7 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1851 (William Lassell)",
                        "Missions": "Voyager 2",
                        "Trivia": "Darkest Uranian moon"
                    }
                },
                {
                    "name": "Titania",
                    "mass": 3.527e21,
                    "radius": 788.9,
                    "orbit_radius": 436300,
                    "orbital_period": 8.706,
                    "eccentricity": 0.0011,
                    "facts": {
                        "Radius": "788.9 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1787 (William Herschel)",
                        "Missions": "Voyager 2",
                        "Trivia": "Largest Uranian moon"
                    }
                },
                {
                    "name": "Oberon",
                    "mass": 3.014e21,
                    "radius": 761.4,
                    "orbit_radius": 583500,
                    "orbital_period": 13.463,
                    "eccentricity": 0.0014,
                    "facts": {
                        "Radius": "761.4 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1787 (William Herschel)",
                        "Missions": "Voyager 2",
                        "Trivia": "Features large craters"
                    }
                }
            ],
            "facts": {
                "Radius": "25362 km",
                "Composition": "Gas (hydrogen, helium, methane)",
                "Discovery": "1781 (William Herschel)",
                "Missions": "Voyager 2 (1986)",
                "Trivia": "Axis tilted 98 degrees"
            }
        },
        {
            "name": "Neptune",
            "mass": 1.024e26,
            "radius": 24622,
            "orbit_radius": 4495.06e6,
            "orbital_period": 59800.00,
            "eccentricity": 0.0113,
            "color": PLANET_COLORS[7],
            "moons": [
                {
                    "name": "Triton",
                    "mass": 2.140e22,
                    "radius": 1353.4,
                    "orbit_radius": 354760,
                    "orbital_period": -5.877,
                    "eccentricity": 0.000016,
                    "facts": {
                        "Radius": "1353.4 km",
                        "Composition": "Ice, rock, nitrogen frost",
                        "Discovery": "1846 (William Lassell)",
                        "Missions": "Voyager 2",
                        "Trivia": "Retrograde orbit, likely captured"
                    }
                }
            ],
            "facts": {
                "Radius": "24622 km",
                "Composition": "Gas (hydrogen, helium, methane)",
                "Discovery": "1846 (Le Verrier, Galle)",
                "Missions": "Voyager 2 (1989)",
                "Trivia": "Strongest winds in Solar System"
            }
        },
        {
            "name": "Pluto",
            "mass": 1.309e22,
            "radius": 1188,
            "orbit_radius": 5906.38e6,
            "orbital_period": 90560,
            "eccentricity": 0.2488,
            "color": DWARF_PLANET_COLORS["Pluto"],
            "moons": [
                {
                    "name": "Charon",
                    "mass": 1.586e21,
                    "radius": 606,
                    "orbit_radius": 19640,
                    "orbital_period": 6.387,
                    "eccentricity": 0.0,
                    "facts": {
                        "Radius": "606 km",
                        "Composition": "Ice, rock",
                        "Discovery": "1978 (James Christy)",
                        "Missions": "New Horizons (2015)",
                        "Trivia": "Forms binary system with Pluto"
                    }
                },
                {
                    "name": "Nix",
                    "mass": 4.5e16,
                    "radius": 23,
                    "orbit_radius": 48694,
                    "orbital_period": 24.854,
                    "eccentricity": 0.002,
                    "facts": {
                        "Radius": "23 km",
                        "Composition": "Ice",
                        "Discovery": "2005 (Weaver, Stern)",
                        "Missions": "New Horizons",
                        "Trivia": "Small, irregular shape"
                    }
                },
                {
                    "name": "Hydra",
                    "mass": 4.8e16,
                    "radius": 30.5,
                    "orbit_radius": 64738,
                    "orbital_period": 38.202,
                    "eccentricity": 0.005,
                    "facts": {
                        "Radius": "30.5 km",
                        "Composition": "Ice",
                        "Discovery": "2005 (Weaver, Stern)",
                        "Missions": "New Horizons",
                        "Trivia": "Elongated shape"
                    }
                },
                {
                    "name": "Kerberos",
                    "mass": 1.6e16,
                    "radius": 14,
                    "orbit_radius": 57783,
                    "orbital_period": 32.167,
                    "eccentricity": 0.003,
                    "facts": {
                        "Radius": "14 km",
                        "Composition": "Ice",
                        "Discovery": "2011 (Showalter)",
                        "Missions": "New Horizons",
                        "Trivia": "Faint, small moon"
                    }
                },
                {
                    "name": "Styx",
                    "mass": 7.5e15,
                    "radius": 10,
                    "orbit_radius": 42656,
                    "orbital_period": 20.161,
                    "eccentricity": 0.006,
                    "facts": {
                        "Radius": "10 km",
                        "Composition": "Ice",
                        "Discovery": "2012 (Showalter)",
                        "Missions": "New Horizons",
                        "Trivia": "Smallest Plutonian moon"
                    }
                }
            ],
            "facts": {
                "Radius": "1188 km",
                "Composition": "Ice (nitrogen, methane), rock",
                "Discovery": "1930 (Clyde Tombaugh)",
                "Missions": "New Horizons (2015)",
                "Trivia": "Reclassified as dwarf planet (2006)"
            }
        },
        {
            "name": "Eris",
            "mass": 1.66e22,
            "radius": 1163,
            "orbit_radius": 10159.8e6,
            "orbital_period": 203670,
            "eccentricity": 0.436,
            "color": DWARF_PLANET_COLORS["Eris"],
            "moons": [
                {
                    "name": "Dysnomia",
                    "mass": 1.5e20,
                    "radius": 175,
                    "orbit_radius": 37350,
                    "orbital_period": 15.774,
                    "eccentricity": 0.013,
                    "facts": {
                        "Radius": "175 km",
                        "Composition": "Ice",
                        "Discovery": "2005 (Brown)",
                        "Missions": "None",
                        "Trivia": "Named after Eris's daughter"
                    }
                }
            ],
            "facts": {
                "Radius": "1163 km",
                "Composition": "Ice, rock",
                "Discovery": "2005 (Brown, Trujillo, Rabinowitz)",
                "Missions": "None",
                "Trivia": "More massive than Pluto"
            }
        },
        {
            "name": "Haumea",
            "mass": 4.006e21,
            "radius": 816,
            "orbit_radius": 6452.2e6,
            "orbital_period": 103660,
            "eccentricity": 0.194,
            "color": DWARF_PLANET_COLORS["Haumea"],
            "moons": [
                {
                    "name": "Hi’iaka",
                    "mass": 1.79e19,
                    "radius": 160,
                    "orbit_radius": 49880,
                    "orbital_period": 49.12,
                    "eccentricity": 0.051,
                    "facts": {
                        "Radius": "160 km",
                        "Composition": "Ice",
                        "Discovery": "2005 (Brown)",
                        "Missions": "None",
                        "Trivia": "Named after Hawaiian goddess"
                    }
                },
                {
                    "name": "Namaka",
                    "mass": 1.79e18,
                    "radius": 85,
                    "orbit_radius": 25657,
                    "orbital_period": 18.28,
                    "eccentricity": 0.103,
                    "facts": {
                        "Radius": "85 km",
                        "Composition": "Ice",
                        "Discovery": "2005 (Brown)",
                        "Missions": "None",
                        "Trivia": "Named after Hawaiian sea goddess"
                    }
                }
            ],
            "facts": {
                "Radius": "816 km",
                "Composition": "Ice, rock",
                "Discovery": "2004 (Brown)",
                "Missions": "None",
                "Trivia": "Oblate shape due to fast rotation"
            }
        },
        {
            "name": "Makemake",
            "mass": 3.1e21,
            "radius": 715,
            "orbit_radius": 6834.7e6,
            "orbital_period": 111690,
            "eccentricity": 0.159,
            "color": DWARF_PLANET_COLORS["Makemake"],
            "facts": {
                "Radius": "715 km",
                "Composition": "Ice (methane, ethane), rock",
                "Discovery": "2005 (Brown)",
                "Missions": "None",
                "Trivia": "Named after Rapa Nui creator god"
            }
        },
        {
            "name": "Quaoar",
            "mass": 1.4e21,
            "radius": 555,
            "orbit_radius": 6534.1e6,
            "orbital_period": 105120,
            "eccentricity": 0.038,
            "color": DWARF_PLANET_COLORS["Quaoar"],
            "moons": [
                {
                    "name": "Weywot",
                    "mass": 1.4e18,
                    "radius": 85,
                    "orbit_radius": 14500,
                    "orbital_period": 12.438,
                    "eccentricity": 0.14,
                    "facts": {
                        "Radius": "85 km",
                        "Composition": "Ice",
                        "Discovery": "2007 (Brown)",
                        "Missions": "None",
                        "Trivia": "Named after Tongva sky god's son"
                    }
                }
            ],
            "facts": {
                "Radius": "555 km",
                "Composition": "Ice, rock",
                "Discovery": "2002 (Brown, Trujillo)",
                "Missions": "None",
                "Trivia": "Named after Tongva creator god"
            }
        },
        {
            "name": "Orcus",
            "mass": 6.41e20,
            "radius": 458,
            "orbit_radius": 5894.8e6,
            "orbital_period": 89425,
            "eccentricity": 0.226,
            "color": DWARF_PLANET_COLORS["Orcus"],
            "moons": [
                {
                    "name": "Vanth",
                    "mass": 9.0e19,
                    "radius": 221,
                    "orbit_radius": 9000,
                    "orbital_period": 9.54,
                    "eccentricity": 0.007,
                    "facts": {
                        "Radius": "221 km",
                        "Composition": "Ice",
                        "Discovery": "2007 (Brown)",
                        "Missions": "None",
                        "Trivia": "Named after Etruscan deity"
                    }
                }
            ],
            "facts": {
                "Radius": "458 km",
                "Composition": "Ice, rock",
                "Discovery": "2004 (Brown, Trujillo, Rabinowitz)",
                "Missions": "None",
                "Trivia": "Anti-Pluto, orbits opposite Pluto"
            }
        },
        {
            "name": "Ceres",
            "mass": 9.38e20,
            "radius": 473,
            "orbit_radius": 414.0e6,
            "orbital_period": 1680,
            "eccentricity": 0.075,
            "color": DWARF_PLANET_COLORS["Ceres"],
            "facts": {
                "Radius": "473 km",
                "Composition": "Rock, ice",
                "Discovery": "1801 (Giuseppe Piazzi)",
                "Missions": "Dawn (2015–2018)",
                "Trivia": "Largest asteroid, only dwarf planet in asteroid belt"
            }
        },
        {
            "name": "Gonggong",
            "mass": 1.75e21,
            "radius": 615,
            "orbit_radius": 10092.3e6,
            "orbital_period": 202210,
            "eccentricity": 0.503,
            "color": DWARF_PLANET_COLORS["Gonggong"],
            "moons": [
                {
                    "name": "Xiangliu",
                    "mass": 1.0e19,
                    "radius": 100,
                    "orbit_radius": 24000,
                    "orbital_period": 25.2,
                    "eccentricity": 0.29,
                    "facts": {
                        "Radius": "100 km",
                        "Composition": "Ice",
                        "Discovery": "2010 (Schwamb)",
                        "Missions": "None",
                        "Trivia": "Named after Chinese serpent deity"
                    }
                }
            ],
            "facts": {
                "Radius": "615 km",
                "Composition": "Ice, rock",
                "Discovery": "2007 (Schwamb, Brown, Rabinowitz)",
                "Missions": "None",
                "Trivia": "Highly eccentric orbit"
            }
        },
        {
            "name": "Sedna",
            "mass": 1.0e21,
            "radius": 498,
            "orbit_radius": 75679.2e6,
            "orbital_period": 4161000,
            "eccentricity": 0.855,
            "color": DWARF_PLANET_COLORS["Sedna"],
            "facts": {
                "Radius": "498 km",
                "Composition": "Ice, rock",
                "Discovery": "2003 (Brown, Trujillo, Rabinowitz)",
                "Missions": "None",
                "Trivia": "Most distant known orbit (~76–936 AU)"
            }
        },
        {
            "name": "Salacia",
            "mass": 4.38e20,
            "radius": 423,
            "orbit_radius": 6314.8e6,
            "orbital_period": 100010,
            "eccentricity": 0.106,
            "color": DWARF_PLANET_COLORS["Salacia"],
            "moons": [
                {
                    "name": "Actaea",
                    "mass": 1.2e19,
                    "radius": 150,
                    "orbit_radius": 5700,
                    "orbital_period": 5.493,
                    "eccentricity": 0.008,
                    "facts": {
                        "Radius": "150 km",
                        "Composition": "Ice",
                        "Discovery": "2006 (Noll)",
                        "Missions": "None",
                        "Trivia": "Named after sea nymph"
                    }
                }
            ],
            "facts": {
                "Radius": "423 km",
                "Composition": "Ice, rock",
                "Discovery": "2004 (Noll, Stephens, Grundy)",
                "Missions": "None",
                "Trivia": "Named after Roman sea goddess"
            }
        }
    ]

    sun = solar_system.add_star(
        x=center_x,
        y=center_y,
        radius=sun_pixel_radius,
        color=planets[0]["color"],
        name=planets[0]["name"],
        mass=planets[0]["mass"],
        facts=planets[0]["facts"]
    )

    earth_period = 365.26
    base_frames = 3600
    base_speed = 2 * math.pi / base_frames

    for i in range(1, len(planets)):
        semi_major_axis_pixels = planets[i]["orbit_radius"] * distance_scale
        real_radius_km = planets[i]["radius"]
        pixel_radius = max(1, 1 + 8 * math.log10(real_radius_km / 1000))
        period_days = planets[i]["orbital_period"]
        orbit_speed = base_speed * (earth_period / period_days) if period_days > 0 else 0
        color = planets[i]["color"] if i <= 8 else DWARF_PLANET_COLORS[planets[i]["name"]]
        eccentricity = planets[i]["eccentricity"]
        planet = solar_system.add_planet(
            parent=sun,
            semi_major_axis=semi_major_axis_pixels,
            radius=pixel_radius,
            color=color,
            orbit_speed=orbit_speed,
            eccentricity=eccentricity,
            name=planets[i]["name"],
            mass=planets[i]["mass"],
            facts=planets[i]["facts"]
        )

        if "moons" in planets[i]:
            for moon_data in planets[i]["moons"]:
                moon_semi_major_axis = moon_data["orbit_radius"] * distance_scale
                moon_real_radius = moon_data["radius"]
                moon_pixel_radius = max(0.5, 0.5 + 5 * math.log10(moon_real_radius / 1000))
                moon_period = moon_data["orbital_period"]
                moon_speed = base_speed * (earth_period / abs(moon_period)) * (-1 if moon_period < 0 else 1)
                moon_eccentricity = moon_data["eccentricity"]
                solar_system.add_moon(
                    parent=planet,
                    semi_major_axis=moon_semi_major_axis,
                    radius=moon_pixel_radius,
                    orbit_speed=moon_speed,
                    eccentricity=moon_eccentricity,
                    name=moon_data["name"],
                    mass=moon_data["mass"],
                    facts=moon_data["facts"]
                )

    return solar_system

def main():
    global screen, WIDTH, HEIGHT
    solar_system = create_real_solar_system(WIDTH, HEIGHT)
    clock = pygame.time.Clock()
    running = True
    paused = False
    view_x, view_y = WIDTH // 2, HEIGHT // 2
    zoom = 1.0
    dragging = False
    last_mouse_pos = (0, 0)
    selected_body = None
    info_surface = None
    last_fps = -1
    last_time_factor = -1
    last_planet_count = -1
    last_moon_count = -1

    while running:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                view_x, view_y = WIDTH // 2, HEIGHT // 2
                for body in solar_system.bodies:
                    body.last_zoom = -1
                    body.orbit_surface = None
                    body.facts_surface = None
                info_surface = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    solar_system.time_factor = min(solar_system.time_factor * 1.5, 100)
                elif event.key == pygame.K_MINUS:
                    solar_system.time_factor = max(solar_system.time_factor / 1.5, 0.01)
                elif event.key == pygame.K_r:
                    solar_system = create_real_solar_system(WIDTH, HEIGHT)
                    view_x, view_y = WIDTH // 2, HEIGHT // 2
                    zoom = 1.0
                    selected_body = None
                    info_surface = None
                elif event.key == pygame.K_i:
                    zoom *= 1.1
                    zoom = max(0.05, min(zoom, 5.0))
                elif event.key == pygame.K_o:
                    zoom *= 0.909
                    zoom = max(0.05, min(zoom, 5.0))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    last_mouse_pos = event.pos
                    for body in solar_system.bodies:
                        scaled_x = (body.x - view_x) * zoom + WIDTH // 2
                        scaled_y = (body.y - view_y) * zoom + HEIGHT // 2
                        scaled_radius = body.radius * zoom
                        dist = math.hypot(mouse_pos[0] - scaled_x, mouse_pos[1] - scaled_y)
                        if dist <= max(scaled_radius, 10):
                            if selected_body == body:
                                selected_body = None
                            else:
                                selected_body = body
                            break
                    else:
                        selected_body = None
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                dx, dy = event.pos[0] - last_mouse_pos[0], event.pos[1] - last_mouse_pos[1]
                view_x -= dx / zoom
                view_y -= dy / zoom
                last_mouse_pos = event.pos

        if not paused:
            solar_system.update()

        screen.fill(BLACK)
        solar_system.draw(screen, zoom, view_x, view_y, WIDTH, HEIGHT)

        if selected_body:
            selected_body.update_facts_surface(WIDTH, HEIGHT)
            if selected_body.facts_surface:
                facts_x = mouse_pos[0] + 20
                facts_y = mouse_pos[1] + 20
                if facts_x + selected_body.facts_surface.get_width() > WIDTH:
                    facts_x = mouse_pos[0] - selected_body.facts_surface.get_width() - 20
                if facts_y + selected_body.facts_surface.get_height() > HEIGHT:
                    facts_y = mouse_pos[1] - selected_body.facts_surface.get_height() - 20
                screen.blit(selected_body.facts_surface, (facts_x, facts_y))

        if (info_surface is None or
            int(clock.get_fps()) != last_fps or
            solar_system.time_factor != last_time_factor or
            len(solar_system.planets) != last_planet_count or
            len(solar_system.moons) != last_moon_count):
            last_fps = int(clock.get_fps())
            last_time_factor = solar_system.time_factor
            last_planet_count = len(solar_system.planets)
            last_moon_count = len(solar_system.moons)
            info_text = [
                f"FPS: {last_fps}",
                f"Planets: {last_planet_count}",
                f"Moons: {last_moon_count}",
                f"Time Scale: {last_time_factor:.1f}x",
                "",
                "Controls:",
                "Space - Pause/Resume",
                "+/- - Adjust speed",
                "I/O - Zoom",
                "Drag - Pan",
                "Click - Show facts",
                "R - Reset simulation",
                "ESC - Exit"
            ]
            max_width = max(font.size(text)[0] for text in info_text) + 20
            info_height = len(info_text) * 22 + 20
            info_surface = pygame.Surface((max_width, info_height), pygame.SRCALPHA)
            for i, text in enumerate(info_text):
                text_surf = font.render(text, True, WHITE)
                info_surface.blit(text_surf, (10, 10 + i * 22))
        screen.blit(info_surface, (10, 10))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
