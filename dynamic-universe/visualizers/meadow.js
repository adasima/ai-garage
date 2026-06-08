
export const meadow = {
    mount: (canvas) => {
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        let animationId;
        const grassArray = [];
        const petalsArray = [];
        const numberOfGrass = 400;
        const numberOfPetals = 50;

        const mouse = { x: 0, y: 0, active: false };
        let wind = 0;
        let time = 0;

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            init();
        };

        const handleMouseMove = (e) => {
            mouse.x = e.x;
            mouse.y = e.y;
            mouse.active = true;
        };

        window.addEventListener('resize', handleResize);
        canvas.addEventListener('mousemove', handleMouseMove);

        class Grass {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = canvas.height;
                this.height = Math.random() * 150 + 50;
                this.width = Math.random() * 4 + 2;
                this.angle = 0;
                this.lean = (Math.random() - 0.5) * 5; // Natural lean
                this.color = `hsl(${Math.random() * 40 + 80}, 70%, ${Math.random() * 20 + 30}%)`;
            }
            draw() {
                // Calculate tip position based on wind and time
                const mouseIdx = (mouse.x - this.x) / 300;
                const dist = Math.abs(mouse.x - this.x);
                let interaction = 0;

                if (dist < 200) {
                    interaction = (1 - dist / 200) * (mouse.x > this.x ? -30 : 30);
                }

                const sway = Math.sin(time + this.x * 0.01) * 15 + interaction;
                const tipX = this.x + this.lean + sway;
                const tipY = this.y - this.height;

                ctx.beginPath();
                ctx.moveTo(this.x, this.y);
                // Control point for the curve
                const cpX = this.x + (tipX - this.x) * 0.5;
                const cpY = this.y - this.height * 0.6;

                ctx.quadraticCurveTo(cpX, cpY, tipX, tipY);
                ctx.strokeStyle = this.color;
                ctx.lineWidth = this.width;
                ctx.lineCap = 'round';
                ctx.stroke();
            }
        }

        class Petal {
            constructor() {
                this.reset();
            }
            reset() {
                this.x = Math.random() * canvas.width;
                this.y = -20;
                this.size = Math.random() * 6 + 4;
                this.speedY = Math.random() * 1 + 0.5;
                this.speedX = Math.random() * 2 - 1;
                this.angle = Math.random() * 360;
                this.spin = Math.random() * 2 - 1;
                this.color = `hsl(${Math.random() * 20 + 340}, 80%, 80%)`; // Soft pinks
            }
            update() {
                this.y += this.speedY;
                this.x += this.speedX + Math.sin(time * 0.5) * 2;
                this.angle += this.spin;
                if (this.y > canvas.height) this.reset();
            }
            draw() {
                ctx.save();
                ctx.translate(this.x, this.y);
                ctx.rotate(this.angle * Math.PI / 180);
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.ellipse(0, 0, this.size, this.size * 0.5, 0, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
        }

        function init() {
            grassArray.length = 0;
            petalsArray.length = 0;
            for (let i = 0; i < numberOfGrass; i++) {
                grassArray.push(new Grass());
            }
            for (let i = 0; i < numberOfPetals; i++) {
                petalsArray.push(new Petal());
            }
        }

        function animate() {
            // Sunny background gradient
            const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
            grad.addColorStop(0, '#87CEEB'); // Sky Blue
            grad.addColorStop(1, '#E0FFE0'); // Light Green
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw grass (back to front sorting can be added, but randomized is fine)
            grassArray.forEach(grass => grass.draw());

            // Draw petals
            petalsArray.forEach(petal => {
                petal.update();
                petal.draw();
            });

            time += 0.02;
            animationId = requestAnimationFrame(animate);
        }

        init();
        animate();

        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener('resize', handleResize);
            canvas.removeEventListener('mousemove', handleMouseMove);
        };
    }
};
