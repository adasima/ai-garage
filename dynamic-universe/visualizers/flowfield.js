
export const flowfield = {
    mount: (canvas) => {
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        let animationId;
        let flowField;
        let pArray = [];
        const numberOfParticles = 700;
        const scale = 20; // grid cell size

        let cols = Math.floor(canvas.width / scale);
        let rows = Math.floor(canvas.height / scale);

        // Settings
        let curve = 1;
        let zoom = 0.05;

        // Mouse for interaction
        const mouse = { x: 0, y: 0, active: false };

        const handleResize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            cols = Math.floor(canvas.width / scale);
            rows = Math.floor(canvas.height / scale);
            initParticles();
        };

        const handleMouseMove = (e) => {
            mouse.x = e.x;
            mouse.y = e.y;
            mouse.active = true;
        };

        window.addEventListener('resize', handleResize);
        canvas.addEventListener('mousemove', handleMouseMove);

        class Particle {
            constructor() {
                this.x = Math.floor(Math.random() * canvas.width);
                this.y = Math.floor(Math.random() * canvas.height);
                // history of positions for trailing
                this.history = [{ x: this.x, y: this.y }];
                this.maxLength = Math.floor(Math.random() * 20 + 5);
                this.timer = this.maxLength * 2;
                this.angle = 0;
                this.speed = Math.random() * 3 + 1;
                this.hue = Math.random() * 360;
            }
            update() {
                this.timer--;
                if (this.timer >= 1) {
                    let x = Math.floor(this.x / scale);
                    let y = Math.floor(this.y / scale);
                    // Safe access
                    let index = x + y * cols;
                    if (flowField[index]) {
                        this.angle = flowField[index];
                    }

                    // Simpler flow logic: just trigonometry based on position
                    // Overwrite flowField for optimization if needed, but here we calculate per frame per particle if flowField static?
                    // Actually let's use the precalculated Grid idea, but simple Trig for now.

                    this.angle += 0; // standard flow

                    // Mouse repulsion/attraction
                    if (mouse.active) {
                        const dx = mouse.x - this.x;
                        const dy = mouse.y - this.y;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        if (dist < 200) {
                            const force = (200 - dist) / 200;
                            this.angle += force * 2; // Disrupt flow
                        }
                    }

                    this.x += Math.cos(this.angle) * this.speed;
                    this.y += Math.sin(this.angle) * this.speed;

                    this.history.push({ x: this.x, y: this.y });
                    if (this.history.length > this.maxLength) {
                        this.history.shift();
                    }
                } else if (this.history.length > 1) {
                    this.history.shift();
                } else {
                    this.reset();
                }
            }
            reset() {
                this.x = Math.floor(Math.random() * canvas.width);
                this.y = Math.floor(Math.random() * canvas.height);
                this.history = [{ x: this.x, y: this.y }];
                this.timer = this.maxLength * 2;
            }
            draw() {
                ctx.beginPath();
                if (this.history.length > 0) {
                    ctx.moveTo(this.history[0].x, this.history[0].y);
                    for (let i = 0; i < this.history.length; i++) {
                        ctx.lineTo(this.history[i].x, this.history[i].y);
                    }
                }
                ctx.strokeStyle = 'hsl(' + this.hue + ', 100%, 50%)';
                ctx.lineWidth = 1;
                ctx.stroke();
            }
        }

        function initParticles() {
            pArray = [];
            for (let i = 0; i < numberOfParticles; i++) {
                pArray.push(new Particle());
            }
        }

        initParticles();

        let time = 0;
        function animate() {
            // Create fading trail effect
            ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Recalculate Flow Field
            flowField = new Float32Array(cols * rows); // optimized array

            for (let y = 0; y < rows; y++) {
                for (let x = 0; x < cols; x++) {
                    let index = x + y * cols;
                    // Dynamic flow angle
                    let angle = (Math.cos(x * zoom) + Math.sin(y * zoom)) * curve;
                    angle += time; // animate the field itself
                    flowField[index] = angle;
                }
            }

            time += 0.005;

            pArray.forEach(p => {
                p.update();
                p.draw();
            });

            animationId = requestAnimationFrame(animate);
        }

        animate();

        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener('resize', handleResize);
            canvas.removeEventListener('mousemove', handleMouseMove);
        };
    }
};
